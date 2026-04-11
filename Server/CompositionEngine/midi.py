from functools import cached_property

import pretty_midi as pm

from Server.CompositionEngine.models import Chord, Song
from Server.utils.composition_utils import INSTRUMENTS_MIDI_CHANNELS, OCTAVES, CHORD_OCTAVES, MIDI_DRUM_PITCHES, \
    DRUM_VELOCITIES, SONG_PARTS, BEATS_PER_BAR, DRUM_TO_PATTERN_MAP, ARPEGGIO_OCTAVES


class Timeline:
    def __init__(self):
        self.current = 0.0

    def advance(self, seconds: float) -> tuple[float, float]:
        start = self.current
        self.current += seconds
        return start, self.current


class MidiEngine:
    def __init__(self, song: Song):
        if not song:
            raise ValueError(f"Invalid song.")
        self._song = song

        self.chords_time = Timeline()  # keep track of how many seconds of the song have been created
        self.melody_time = Timeline()  # keep track of how many seconds of the song have been created
        self.drums_time = Timeline()  # keep track of how many seconds of the song have been created

        self.last_midi_pitch: int | None = None  # keep track of the last midi pitch for octave calculations and more
        self.midi = pm.PrettyMIDI(initial_tempo=song.tempo)  # create midi object

        # add instruments
        self.chords_instrument = pm.Instrument(program=INSTRUMENTS_MIDI_CHANNELS[song.instruments["CHORDS"]])
        self.melody_instrument = pm.Instrument(program=INSTRUMENTS_MIDI_CHANNELS[song.instruments["MELODY"]])
        self.midi.instruments.extend([self.chords_instrument, self.melody_instrument])  # append instruments

        # handle drums
        self.drums_instrument: pm.Instrument | None = None
        if not song.drums.is_empty():  # not all songs have drums
            self.drums_instrument = pm.Instrument(program=0, is_drum=True)  # channel 9
            self.midi.instruments.append(self.drums_instrument)  # append drums

    @cached_property
    def seconds_per_beat(self) -> float:
        """return how many seconds it takes for a beat, provided the tempo"""
        return 60 / self._song.tempo

    def _beats_to_seconds(self, beats: float) -> float:
        """given beats, return how many seconds it is"""
        return beats * self.seconds_per_beat

    @staticmethod
    def _get_midi_pitch(pitch: int, octave: int) -> int:
        """calculate the midi pitch used in pretty midi"""
        return pitch + 12 * octave

    def _get_octave(self, pitch: int) -> int:
        """Returns the octave that makes the note closest to the last midi note"""
        if self.last_midi_pitch is None:
            return 4  # starting octave will always be 4

        best_octave = min(  # get the minimum distance from last note
            OCTAVES,
            # calculate distance
            key=lambda octave: abs(MidiEngine._get_midi_pitch(pitch, octave) - self.last_midi_pitch)
        )

        return best_octave

    def _add_chord(self, chord: Chord):
        """redirect the chord to its _add_X_chord function where it'll be added. X = pattern name"""
        pattern = chord.pattern

        if "SUSTAINED" in pattern:
            self._add_sustained_chord(chord, int(pattern.split()[-1]))  # last char in pattern contains 1, 2 or 4
        elif "ARPEGGIO" in pattern:
            self._add_arpeggio_chord(chord, pattern.split()[1])  # 2nd part of the pattern contains UP or DOWN
        elif "OFFBEAT" in pattern:
            self._add_offbeat_chord(chord)
        elif "WALTZ-LIKE" in pattern:
            self._add_waltz_like_chord(chord)
        elif "STRIDE" in pattern:
            self._add_stride_chord(chord)

    # ------------------------------------------------------------------ #
    #  CHORD PATTERNS                                                    #
    # ------------------------------------------------------------------ #

    def _add_sustained_chord(self, chord: Chord, repeats: int):
        """add all the notes of a sustained chord to the midi.
        sustained chord: all 3 notes of the chord at the exact same time, repeated X times."""
        repeat_beats = chord.BEATS // repeats
        repeat_seconds = self._beats_to_seconds(repeat_beats)

        for _ in range(repeats):
            for note, octave in zip(chord.notes, CHORD_OCTAVES["SUSTAINED"]):  # this loop will always run 3 times
                self._add_note(note.velocity, note.pitch, octave, self.chords_time.current, repeat_seconds,
                               self.chords_instrument)

            self.chords_time.advance(repeat_seconds)

    def _add_arpeggio_chord(self, chord: Chord, direction: str):
        """add all the notes of an arpeggio chord to the midi.
        arpeggio chord: one note of the chord at a time, direction declares if the pitch goes up or down."""
        note_beats = chord.BEATS / 4  # all notes with length of 1 beat (if chord.BEATS is 4)
        note_seconds = self._beats_to_seconds(note_beats)

        # pick the right octaves for each note
        notes = list(chord.notes) + [chord.notes[0]]  # root, 3rd, 5th, root
        last_midi_pitch = self._get_midi_pitch(notes[0].pitch, 3)  # first note starts on octave 3

        # add first note directly at octave 3
        self._add_note(notes[0].velocity, notes[0].pitch, 3, self.chords_time.current,
                       note_seconds, self.chords_instrument)
        self.chords_time.advance(note_seconds)

        # add remaining notes
        for note in notes[1:]:
            # pick the lowest octave that's closest to the last note and is going in the right direction
            note_octave = min(
                ARPEGGIO_OCTAVES,
                key=lambda octave: (
                    abs(self._get_midi_pitch(note.pitch, octave) - last_midi_pitch)
                    # both statements must be the same for the whole statement to produce True
                    if (self._get_midi_pitch(note.pitch, octave) > last_midi_pitch) == (direction == "UP")
                    else float('inf')  # return the largest value, so it's never picked
                )
            )

            # if all octaves were disqualified, pick closest regardless of direction
            if (self._get_midi_pitch(note.pitch, note_octave) > last_midi_pitch) != (direction == "UP"):
                note_octave = min(
                    ARPEGGIO_OCTAVES,
                    key=lambda octave: abs(self._get_midi_pitch(note.pitch, octave) - last_midi_pitch)
                )

            # got octave, now add note
            last_midi_pitch = self._get_midi_pitch(note.pitch, note_octave)
            self._add_note(note.velocity, note.pitch, note_octave, self.chords_time.current,
                           note_seconds, self.chords_instrument)
            self.chords_time.advance(note_seconds)

    def _add_offbeat_chord(self, chord: Chord):
        """add all the notes of an offbeat chord to the midi.
        offbeat chord: all 3 notes of the chord at the exact same time, at the 2nd and 4th beats."""
        note_beats = chord.BEATS / 4  # all notes with length of 1 beat (if chord.BEATS is 4)
        note_seconds = self._beats_to_seconds(note_beats)

        for _ in range(2):
            self.chords_time.advance(note_seconds)  # skip a beat

            for note, octave in zip(chord.notes, CHORD_OCTAVES["OFFBEAT"]):
                self._add_note(note.velocity, note.pitch, octave, self.chords_time.current, note_seconds,
                               self.chords_instrument)

            self.chords_time.advance(note_seconds)

    def _add_waltz_like_chord(self, chord: Chord):
        """add all the notes of a waltz-like chord to the midi.
        waltz-like chord: at the 1st beat only the root note, and all other beats play the other notes."""
        note_beats = chord.BEATS * 0.75 / 4  # all notes with length of 0.75 beats (if chord.BEATS is 4)
        note_seconds = self._beats_to_seconds(note_beats)

        # add the first note
        first_note = chord.notes[0]
        self._add_note(first_note.velocity, first_note.pitch, CHORD_OCTAVES["WALTZ-LIKE"][0], self.chords_time.current,
                       note_seconds, self.chords_instrument)
        self.chords_time.advance(note_seconds)
        self.chords_time.advance(self._beats_to_seconds(1) - note_seconds)  # round to 1 beat

        for _ in range(3):
            for note, octave in zip(chord.notes[1:], CHORD_OCTAVES["WALTZ-LIKE"][1:]):  # skip first note data
                self._add_note(note.velocity, note.pitch, octave, self.chords_time.current, note_seconds,
                               self.chords_instrument)

            self.chords_time.advance(note_seconds)
            self.chords_time.advance(self._beats_to_seconds(1) - note_seconds)  # round to 1 beat

    def _add_stride_chord(self, chord: Chord):
        """add all the notes of a stride chord to the midi.
        stride chord: at the 1st and 3rd beat only the root note, and the 2nd and 4th beat the other notes."""
        note_beats = chord.BEATS * 0.75 / 4  # all notes with length of 0.75 beats (if chord.BEATS is 4)
        note_seconds = self._beats_to_seconds(note_beats)

        for _ in range(2):
            # add 1st/3rd beat (one note)
            note = chord.notes[0]
            self._add_note(note.velocity, note.pitch, CHORD_OCTAVES["STRIDE"][0], self.chords_time.current,
                           note_seconds, self.chords_instrument)
            self.chords_time.advance(note_seconds)
            self.chords_time.advance(self._beats_to_seconds(1) - note_seconds)  # round to 1 beat

            # add the 2nd/4th beat (2 notes)
            for note, octave in zip(chord.notes[1:], CHORD_OCTAVES["STRIDE"][1:]):
                self._add_note(note.velocity, note.pitch, octave, self.chords_time.current, note_seconds,
                               self.chords_instrument)
            self.chords_time.advance(note_seconds)
            self.chords_time.advance(self._beats_to_seconds(1) - note_seconds)  # round to 1 beat

    def _add_note(self, velocity: int, pitch: int, octave: int, start_time: float, seconds: float,
                  instrument: pm.Instrument) -> int:
        """create a new midi note object and add it to the provided instrument. returns the end time.
        returns last_midi_pitch for it to be kept inside self only whenever a melody note calls it."""

        last_midi_pitch = self._get_midi_pitch(pitch, octave)

        new_midi_note = pm.Note(
            velocity=velocity,
            pitch=last_midi_pitch + 12,  # for any note: bounce it up an octave so it will sound clearer.
            start=start_time,
            end=start_time + seconds
        )

        instrument.notes.append(new_midi_note)

        return last_midi_pitch

    # ------------------------------------------------------------------ #
    #  DRUMS                                                             #
    # ------------------------------------------------------------------ #

    def _add_drums(self, part_name: str):
        """redirect the drums to its _add_X_drums function where it'll be added. X = pattern name"""
        if part_name == "BRIDGE":
            pattern = self._song.drums.bridge_pattern
        else:
            pattern = self._song.drums.main_pattern

        pattern_dict, fill_parts = DRUM_TO_PATTERN_MAP[pattern]
        self._add_drums_pattern(pattern_dict, part_name, self._song.beats[part_name], fill_parts)

    def _add_drums_pattern(self, pattern_dict: dict, part_name: str, part_beats: int, fill_parts: set):
        """add all the notes of the provided drum pattern to the midi."""
        has_fill = part_name in fill_parts
        pattern_beats = part_beats - BEATS_PER_BAR if has_fill else part_beats

        # main pattern
        for _ in range(pattern_beats // BEATS_PER_BAR):
            for half_beat_drums in pattern_dict["MAIN"]:
                for drum in half_beat_drums:
                    self._add_drums_note(drum)

                self.drums_time.advance(self._beats_to_seconds(0.5))

        # fill
        if has_fill:
            for beat_drums in pattern_dict["FILL"]:
                for drum in beat_drums:
                    self._add_drums_note(drum)

                self.drums_time.advance(self._beats_to_seconds(1))

    def _add_drums_note(self, drum: str):
        velocity = DRUM_VELOCITIES[drum]
        pitch = MIDI_DRUM_PITCHES[drum]

        new_midi_note = pm.Note(
            velocity=velocity,
            pitch=pitch,
            start=self.drums_time.current,
            end=self.drums_time.current + self._beats_to_seconds(1)  # doesn't really matter for drums
        )
        self.drums_instrument.notes.append(new_midi_note)

    def generate_midi(self) -> pm.PrettyMIDI:
        """adds all notes to the pretty midi object and returns it."""

        # add chords
        for chord in self._song.chords:
            self._add_chord(chord)

        # add melody
        for note in self._song.melody:
            seconds = self._beats_to_seconds(note.beats)
            self.last_midi_pitch = self._add_note(note.velocity, note.pitch, self._get_octave(note.pitch),
                                                  self.melody_time.current, seconds, self.melody_instrument)
            self.melody_time.advance(seconds)

        # drums
        if not self._song.drums.is_empty():
            for part_name in SONG_PARTS:
                self._add_drums(part_name)

        return self.midi
