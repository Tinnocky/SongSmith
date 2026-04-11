import math
import random
from collections import Counter

from Server.CompositionEngine.models import Note, Chord, Drums, Song
from Server.CompositionEngine.theory import Ruleset
from Server.utils.composition_utils import BASE_NOTE_VELOCITY_WEIGHTS, DRUM_MAIN_PATTERNS, NOTE_VELOCITIES, \
    BASE_NOTE_BEATS_WEIGHTS, NOTE_BEATS, VELOCITY_BEAT_SHIFTS, VELOCITY_DEGREE_SHIFTS, get_beat_position, \
    CHORD_PATTERN_MULTIPLIERS, BASE_CHORD_PATTERN_WEIGHTS, BEATS_PER_BAR, SONG_PARTS


class Generator:
    def __init__(self, ruleset: Ruleset):
        if not ruleset:
            raise ValueError(f"Invalid Ruleset: Cannot be None.")
        self._ruleset = ruleset

    # generating
    def generate_song(self) -> Song:
        """generate a full song object and return it. generate one chord,
        then an amount of melody notes that will fill that whole chord, then repeat."""
        # generate all parts
        # each part contains all the song generated up that point, so the ending contains the full song.
        chords, melody = [], []
        for part in SONG_PARTS:
            chords, melody = self._generate_part(part, self._ruleset.beats[part], chords, melody)

        # get drums, choose main pattern and bridge pattern.
        if not self._ruleset.has_drums:  # no drums at all, create an object with no arguments
            drums = Drums()
        else:  # need to get patterns
            main_pattern, bridge_pattern = self._get_drum_patterns()
            drums = Drums(main_pattern, bridge_pattern)

        # return as a song object
        return Song(chords, melody, drums, self._ruleset.tempo, self._ruleset.instruments, self._ruleset.beats)

    def _generate_part(self, part_name: str, part_length_beats: int, previous_chords: list[Chord],
                       previous_melody: list[Note]) -> tuple[list[Chord], list[Note]]:
        """generate a list of chords and melody for this respective part and return it."""
        chords, melody = list(previous_chords), list(previous_melody)
        beats_generated = 0  # counting this part only
        melody_length_beats = 0
        pattern = self._get_chord_pattern(part_name)  # decide chord pattern for this part

        # generation loop
        while beats_generated < part_length_beats:
            beat_position = get_beat_position(beats_generated)

            # generate 1 chord for this bar
            new_chord = self._rnd_chord(chords, beat_position, pattern)
            chords.append(new_chord)

            # total_beats_generated sums up the chord's length, and the melody can't pass it.
            beats_generated += new_chord.BEATS

            # generate notes until they reach the end of the new_chord
            while melody_length_beats < beats_generated:
                max_beats = beats_generated - melody_length_beats  # largest duration possible for next note
                melody_beat_position = get_beat_position(melody_length_beats)
                new_note = self._rnd_note(chords[-1], melody, melody_beat_position, max_beats)
                melody.append(new_note)

                melody_length_beats += new_note.beats

        # change the last note of the whole song to be the root note
        if part_name == "ENDING":
            melody[-1].note_name = self._ruleset.legal_notes[0]  # root note
            melody[-1].degree = 1  # set it to the first degree

        return chords, melody

    # chords
    def _rnd_chord(self, previous_chords: list[Chord] | None, beat_position: float, pattern: str) -> Chord:
        """Return the next chord based on the ruleset and previous chords."""
        degree = self._get_chord_degree(previous_chords)
        # velocity = self._get_velocity(degree, beat_position, offset=-20)

        notes = []
        triad = self._ruleset.legal_triads[degree - 1]

        for i in range(3):
            notes.append(Note(
                triad[i],
                self._ruleset.scale_data["TRIADS"][degree - 1][i],
                None,  # type: ignore
                60  # chords will always have this velocity
            ))

        return Chord(notes, degree, pattern)

    def _get_chord_degree(self, previous_chords: list[Chord] | None) -> int:
        """chosen and return the chord's degree from 1-7."""
        total_chords = self._ruleset.sum_of_beats // BEATS_PER_BAR
        if not previous_chords:  # first chord of the song will start on 1st or 4th
            return random.choice([1, 4])

        if len(previous_chords) == total_chords - 1:  # last chord of the song will resolve to 1st
            return 1

        # run weights to decide chord
        last_degree = previous_chords[-1].degree
        allowed = self._ruleset.get_allowed_next(last_degree)
        weights = {degree: 1.0 for degree in allowed}

        # anti repetition
        recent_degrees = [chord.degree for chord in previous_chords[-4:]]  # last 4 chord's degrees
        for degree in weights:
            count = recent_degrees.count(degree)
            if count > 0:
                weights[degree] *= 0.5 ** count  # more repeats, way less likely

        # complexity
        complexity = self._ruleset.complexity
        primary = {1, 4, 5}  # these are the "simple" ones
        for degree in weights:
            if complexity == "SIMPLE" and degree not in primary:
                weights[degree] *= 0.3
            elif complexity == "COMPLEX" and degree not in primary:
                weights[degree] *= 2.0

        # second to last chord of the song
        if len(previous_chords) == total_chords - 2:
            scale = self._ruleset.scale_name

            # these chords are possible second to last chords,
            # in order to make the transition to the 1st feel more natural.
            second_to_last_chords = {
                "MAJOR": {5: 2.0, 7: 1.5, 4: 1.2},
                "MINOR": {7: 2.0, 4: 1.5, 6: 1.2},
                "MIXOLYDIAN": {7: 2.0, 4: 1.5, 5: 1.2},
            }.get(scale)

            for degree, bias in second_to_last_chords.items():
                if degree in weights:
                    weights[degree] *= bias

        # choose
        return random.choices(list(weights.keys()), weights=list(weights.values()))[0]

    def _get_chord_pattern(self, current_song_part: str) -> str:
        """choose and return the chord's pattern from CHORD_PATTERNS.
        used only once per song part."""
        weights = BASE_CHORD_PATTERN_WEIGHTS.copy()

        # determine if the tempo is either slow, fast, or anywhere inbetween
        tempo = "slow" if self._ruleset.tempo < 80 else "fast" if self._ruleset.tempo > 140 else None

        # get the right parameters for this chord
        params = [
            CHORD_PATTERN_MULTIPLIERS["complexity"].get(self._ruleset.complexity),
            CHORD_PATTERN_MULTIPLIERS["instrument"].get(self._ruleset.instruments["CHORDS"]),
            CHORD_PATTERN_MULTIPLIERS["scale"].get(self._ruleset.scale_name),
            CHORD_PATTERN_MULTIPLIERS["tempo"].get(tempo),
            CHORD_PATTERN_MULTIPLIERS["drums"].get(self._ruleset.has_drums),
            CHORD_PATTERN_MULTIPLIERS["song_part"].get(current_song_part),
        ]

        # apply multipliers to weights
        for multipliers in params:
            if multipliers is None:  # cuz of medium tempo and medium complexity multiplier being "None"
                continue
            for pattern, multiplier in multipliers.items():
                if pattern in weights:
                    weights[pattern] *= multiplier

        # choose a pattern
        for pattern in weights:
            weights[pattern] = max(weights[pattern], 0.01)  # so everything will still have a chance

        return random.choices(list(weights.keys()), weights=list(weights.values()))[0]

    # notes
    def _rnd_note(self, current_chord: Chord, previous_melody: list[Note] | None,
                  beat_position: float, max_length: float) -> Note:
        """Return the next note for the melody, determined by the current chord,
        current beat, and more... see helper functions"""
        degree = self._get_note_degree(current_chord, previous_melody, beat_position)
        duration = self._get_note_beats(current_chord, max_length)
        velocity = self._get_velocity(degree, beat_position)
        note_name = self._ruleset.legal_notes[degree - 1]

        return Note(note_name, degree, duration, velocity)

    @staticmethod
    def _get_note_degree(current_chord: Chord, previous_melody: list[Note], beat_position: float) -> int:
        """choose and return the note's degree from 1-7"""
        weights = {degree: 1.0 for degree in range(1, 8)}

        # boost chord notes (and lessen other notes)
        triad_degrees = {note.degree for note in current_chord.notes}
        for degree in weights:
            if degree in triad_degrees:
                weights[degree] *= 1.5
            else:
                weights[degree] *= 0.5

        # boost notes 1 or 2 steps close to the last note
        last_degree = previous_melody[-1].degree if previous_melody else None
        if last_degree:
            for degree in weights:
                distance = abs(degree - last_degree)  # calculate steps distance
                weights[degree] *= 1.6

        # anti repetition
        if previous_melody:
            degree_counter = Counter(note.degree for note in previous_melody[-4:])

            for degree in weights:
                weights[degree] *= 0.7 ** degree_counter.get(degree, 0)

        # beat position
        for degree in weights:
            if beat_position == 1:  # boost chord notes
                if degree in triad_degrees:
                    weights[degree] *= 1.4
            elif beat_position == 2 or beat_position == 4:
                if degree not in triad_degrees:
                    weights[degree] *= 1.4

        return random.choices(list(weights.keys()), weights=list(weights.values()))[0]

    def _get_note_beats(self, current_chord: Chord, max_duration: float) -> float:
        """choose and return the note's duration in beats"""
        weights = BASE_NOTE_BEATS_WEIGHTS.copy()
        multipliers = {duration: 1.0 for duration in weights.keys()}

        # pattern
        chord_pattern = current_chord.pattern
        if chord_pattern == "ARPEGGIO UP" or chord_pattern == "ARPEGGIO DOWN":
            multipliers[2.0] *= 1.4
            multipliers[4.0] *= 1.4
        elif chord_pattern == "OFFBEAT" or chord_pattern == "STRIDE":
            multipliers[2.0] *= 1.7
            multipliers[4.0] *= 1.7
            multipliers[1.5] *= 1.7
            multipliers[0.5] *= 1.4

        # complexity
        if self._ruleset.complexity == "SIMPLE":
            multipliers[1.0] *= 1.5
            multipliers[2.0] *= 1.5
            multipliers[4.0] *= 1.4
        elif self._ruleset.complexity == "COMPLEX":
            multipliers[0.5] *= 1.5
            multipliers[1.0] *= 1.4
            multipliers[1.5] *= 1.4

        # apply multipliers
        for duration in weights:
            weights[duration] *= multipliers[duration]

        # shut off durations that exceed the max
        for duration in weights.keys():
            if duration > max_duration:
                weights[duration] = 0.0

        # if everything is zeroed-out, choose the smallest one (currently 0.5)
        if all(weight == 0.0 for weight in weights.values()):
            return min(NOTE_BEATS)

        return random.choices(list(weights.keys()), weights=list(weights.values()))[0]

    # velocity math
    def _get_velocity(self, degree: int, beat_position: float, offset: int = 0) -> int:
        """choose and return the note's velocity from NOTE_VELOCITIES"""
        shift = 0.0

        # beat position
        shift += VELOCITY_BEAT_SHIFTS.get(beat_position, 0.0)

        # chord degree + scale
        shift += VELOCITY_DEGREE_SHIFTS.get(self._ruleset.scale_name).get(degree, 0.0)

        # tempo
        if self._ruleset.tempo < 80:  # slow
            shift -= 0.3
        elif self._ruleset.tempo > 140:  # fast
            shift += 0.3

        weights = self._apply_shift(BASE_NOTE_VELOCITY_WEIGHTS.copy(), shift)

        choice = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
        return max(min(NOTE_VELOCITIES), min(max(NOTE_VELOCITIES), choice + offset))  # calculate offset and return

    @staticmethod
    def _apply_shift(weights: dict[int, float], shift: float) -> dict[int, float]:
        """weights the dict by applying exponential bias to it using the shift.
        positive shift boosts the possibility of higher values while negative shift does the opposite"""
        biased = {v: w * math.exp(shift * v / 100) for v, w in weights.items()}
        total = sum(biased.values())
        return {v: w / total for v, w in biased.items()}

    def _get_drum_patterns(self) -> tuple[str, str]:
        """return a tuple of the main drum pattern and the bridge drum pattern.
        the main pattern is chosen by the tempo and the bridge is chosen by the main patten itself."""

        weights = {pattern: 1.0 for pattern in DRUM_MAIN_PATTERNS}

        tempo = self._ruleset.tempo
        if tempo < 80:  # slow
            weights["STRAIGHT"] *= 1.5
        elif tempo > 140:  # fast
            weights["ROCK"] *= 1.4
            weights["SYNCOPATED"] *= 1.3

        main_pattern = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
        bridge_pattern = None

        if main_pattern == "STRAIGHT":
            bridge_pattern = "HALF-TIME"
        elif main_pattern == "ROCK":
            bridge_pattern = "STRAIGHT"
        elif main_pattern == "SYNCOPATED":
            bridge_pattern = "SPARSE"

        return main_pattern, bridge_pattern


# test
if __name__ == "__main__":
    rulesets = [
        # Ruleset("C", "MAJOR", 120, "PIANO", "PIANO", 8, 8, True, "MEDIUM")
        Ruleset("G", "MIXOLYDIAN", 120, "SYNTH", "NYLON GUITAR", 12, 12, True, "COMPLEX"),
        Ruleset("A", "MINOR", 90, "NYLON GUITAR", "SYNTH", 4, 8, False, "SIMPLE"),
        Ruleset("F#", "MAJOR", 140, "ROCK GUITAR", "PIANO", 16, 16, True, "COMPLEX"),
        Ruleset("A#", "MINOR", 75, "SYNTH", "SYNTH", 8, 4, False, "MEDIUM"),
        Ruleset("D", "MIXOLYDIAN", 100, "PIANO", "ROCK GUITAR", 4, 4, True, "SIMPLE"),
        Ruleset("B", "MAJOR", 200, "ROCK GUITAR", "ROCK GUITAR", 12, 8, False, "COMPLEX"),
        Ruleset("C#", "MINOR", 1, "NYLON GUITAR", "NYLON GUITAR", 16, 4, True, "SIMPLE"),
        Ruleset("E", "MAJOR", 60, "SYNTH", "PIANO", 8, 16, False, "MEDIUM"),
        Ruleset("G#", "MIXOLYDIAN", 300, "PIANO", "SYNTH", 16, 12, True, "COMPLEX"),
    ]
    print(rulesets)

    for j, rs in enumerate(rulesets, 1):
        print(f"{'=' * 60}")
        print(f"Song {j}: {rs.scale_name} {rs._key} | Tempo {rs.tempo} | {rs.complexity}")  # ignore _key cuz its test
        print(f"{'=' * 60}")

        song = Generator(rs).generate_song()
        print(song)
        print()
