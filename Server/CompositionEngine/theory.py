from functools import cached_property

from Server.utils.composition_utils import SCALES, SCALE_NAMES, NOTES, VERSE_CHORUS_BARS, INSTRUMENTS, COMPLEXITIES, \
    BEATS_PER_BAR


class Ruleset:
    def __init__(self, key: str, scale: str, tempo: int, chords_instrument: str, melody_instrument: str,
                 verse_bars: int, chorus_bars: int, has_drums: bool, complexity: str = "MEDIUM"):
        if key not in NOTES:  # from NOTES
            raise ValueError(f"Invalid root note: {key}. Can only choose from: {NOTES}")
        self._key = key.upper()

        if scale.upper() not in SCALE_NAMES:  # MAJOR, MINOR, MIXOLYDIAN
            raise ValueError(f"Invalid scale: {scale}. Can only choose from: {SCALE_NAMES}")
        self._scale_data = SCALES[scale.upper()]
        self._scale_name = scale.upper()

        if tempo < 1:
            raise ValueError(f"Invalid tempo: {tempo}. Can only be a natural number.")
        self._tempo = tempo

        if complexity not in COMPLEXITIES:  # SIMPLE, MEDIUM, COMPLEX
            raise ValueError(f"Invalid complexity: {complexity}. Can only choose from: {COMPLEXITIES}.")
        self._complexity = complexity

        if not isinstance(has_drums, bool):
            raise ValueError(f"Invalid drums setting: {has_drums}. Can only choose from True, False")
        self._has_drums = has_drums

        # instruments live inside a dict
        if chords_instrument not in INSTRUMENTS:  # PIANO, NYLON GUITAR, ROCK GUITAR, SYNTH
            raise ValueError(f"Invalid chord instrument: {chords_instrument}."
                             f" Can only choose from: {INSTRUMENTS}.")

        if melody_instrument not in INSTRUMENTS:  # PIANO, NYLON GUITAR, ROCK GUITAR, SYNTH
            raise ValueError(f"Invalid melody instrument: {melody_instrument}."
                             f" Can only choose from: {INSTRUMENTS}.")

        self._instruments = {
            "CHORDS": chords_instrument,
            "MELODY": melody_instrument
        }

        # all lengths here live inside a dictionary, as beats
        if verse_bars not in VERSE_CHORUS_BARS:  # 4, 8, 12, 16
            raise ValueError(f"Invalid verse length: {verse_bars}. Can only choose from: {VERSE_CHORUS_BARS}.")

        if chorus_bars not in VERSE_CHORUS_BARS:  # 4, 8, 12, 16
            raise ValueError(f"Invalid chorus length: {chorus_bars}. Can only choose from: {VERSE_CHORUS_BARS}.")

        intro_beats = self._get_edges_bars(verse_bars, chorus_bars) * BEATS_PER_BAR
        verse_beats = verse_bars * BEATS_PER_BAR
        bridge_beats = self._get_bridge_bars(verse_bars, chorus_bars) * BEATS_PER_BAR
        chorus_beats = chorus_bars * BEATS_PER_BAR
        ending_beats = self._get_edges_bars(verse_bars, chorus_bars) * BEATS_PER_BAR

        self._beats = {
            "INTRO": intro_beats,
            "VERSE": verse_beats,
            "BRIDGE": bridge_beats,
            "CHORUS": chorus_beats,
            "ENDING": ending_beats
        }

        # cached properties (see functions right below):
        # legal_notes: list[str]
        # legal_triads: list[list[str]]
        # sum_of_beats: int

    def __repr__(self):
        """string representation. if not triggered before,
        running this will trigger computation (the legal_notes and legal_triads cached properties)"""
        return f"""Ruleset(
            Key & Scale: {self._key} {self._scale_name}
            Tempo: {self._tempo}
            Complexity: {self._complexity}
            Instruments: {self._instruments["CHORDS"]} on chords, {self._instruments["MELODY"]} on melody
            Has Drums: {self._has_drums}
            Length in beats: {self._beats}
            Legal Notes: {self.legal_notes}
            Legal Triads: {self.legal_triads}
        ) \n"""

    @property
    def scale_data(self) -> dict[str, list]:
        return self._scale_data

    @property
    def scale_name(self) -> str:
        return self._scale_name

    @property
    def tempo(self) -> int:
        return self._tempo

    @property
    def complexity(self) -> str:
        return self._complexity

    @property
    def instruments(self) -> dict[str, str]:
        return self._instruments

    @property
    def has_drums(self) -> bool:
        return self._has_drums

    @property
    def beats(self) -> dict[str, int]:
        return self._beats

    @cached_property
    def legal_notes(self) -> list[str]:
        """Return a list of note names in the scale based on the root note (key)."""
        legal_notes = []
        note_index = NOTES.index(self._key)  # get the root note

        for step in self._scale_data["STEPS"]:  # :-1 so the root won't get duplicated
            legal_notes.append(NOTES[note_index])
            note_index = (note_index + step) % 12

        return legal_notes

    @cached_property
    def legal_triads(self) -> list[list[str]]:
        """Returns a list of triads as note names."""
        triads = []

        for triad in self._scale_data["TRIADS"]:
            # get all notes in triad using list comprehension
            triad_notes = [self.legal_notes[degree - 1] for degree in triad]
            triads.append(triad_notes)

        return triads

    @cached_property
    def sum_of_beats(self) -> int:
        """returns the sum of all length (in beats)."""
        return sum(self._beats.values())

    @staticmethod
    def _get_bridge_bars(verse_bars: int, chorus_bars: int) -> int:
        """choose and return the bridge's length in bars based on the verse and chorus lengths.
        the options are 4/8 bars."""
        if verse_bars <= 8 or chorus_bars <= 8:
            return 4  # 4 bars

        return 8  # 8 bars

    @staticmethod
    def _get_edges_bars(verse_bars: int, chorus_bars: int) -> int:
        """choose and return the intro's or ending's length in bars based on the verse and chorus lengths.
        as the intro and ending are shorter, the options are 2/4 bars."""
        if verse_bars <= 4 or chorus_bars <= 4:
            return 2  # 2 bars

        return 4  # 4 bars

    def get_allowed_next(self, chord_index: int) -> list[int]:
        """Returns the allowed_next list of the provided chord"""
        if chord_index < 1 or chord_index > 7:
            raise ValueError(f"Invalid chord_index: {chord_index}. Indexes are 1-indexed and range from 1-7.")

        return self._scale_data["ALLOWED_NEXT"][chord_index - 1]  # -1 because its 0-indexed


# test
if __name__ == "__main__":
    pass  # it works
