from functools import cached_property

from Server.utils.composition_utils import DRUM_MAIN_PATTERNS, DRUM_BRIDGE_PATTERNS, SONG_PARTS, BEATS_PER_BAR
from Server.utils.composition_utils import NOTES, NOTE_BEATS, NOTE_VELOCITIES, PATTERNS


class Note:
    def __init__(self, name: str, degree: int, beats: float | None, velocity: int):
        if name not in NOTES:  # from NOTES
            raise ValueError(f"Invalid note: {name}. Can only choose from: {NOTES}")
        self._name = name
        self._pitch = NOTES.index(self._name)  # 0-11 (representing their placement in the NOTES list)

        if degree < 1 or degree > 7:  # 1-7
            raise ValueError(f"Invalid degree: {degree}. Can only choose from 1-7")
        self._degree = degree

        # beats could be None too for handling chord notes.
        if beats is not None and beats not in NOTE_BEATS:  # from NOTE_BEATS
            raise ValueError(f"Invalid duration: {beats}. Can only choose from {NOTE_BEATS}")
        self._beats: float | None = beats

        if velocity not in NOTE_VELOCITIES:  # from NOTE_VELOCITIES
            raise ValueError(f"Invalid velocity: {velocity}. Can only choose from {NOTE_VELOCITIES}")
        self._velocity = velocity

    def __repr__(self):
        """string representation"""
        return f"""Note(
            name={self._name},
            pitch={self._pitch},
            degree={self._degree},
            beats={self._beats},
            velocity={self._velocity} \n
        )"""

    @property
    def pitch(self) -> int:
        return self._pitch

    @property
    def degree(self) -> int:
        return self._degree

    @property
    def beats(self) -> float | None:
        return self._beats

    @property
    def velocity(self) -> int:
        return self._velocity


class Chord:
    # hardcoded constant properties
    BEATS = BEATS_PER_BAR  # 1 bar

    def __init__(self, notes: list[Note], degree: int, pattern: str):
        if len(notes) != 3:  # only allow triadic chords
            raise ValueError(f"Invalid notes for chord: {notes}. Can only have 3 notes in a chord.")
        self._notes = notes

        if degree < 1 or degree > 7:  # 1-7
            raise ValueError(f"Invalid degree: {degree}. Can only choose from 1-7")
        self._degree = degree

        if pattern not in PATTERNS:  # SUSTAINED 1-4, ARPEGGIO UP/DOWN, OFFBEAT, WALTZ-LIKE, STRIDE
            raise ValueError(f"Invalid pattern: {pattern}. Can only choose from {PATTERNS}")
        self._pattern = pattern

    def __repr__(self):
        """string representation"""
        return f"""Chord(
            length in beats={self.BEATS},
            notes={self._notes},
            degree={self._degree},
            pattern={self._pattern} \n
        )"""

    @property
    def notes(self) -> list[Note]:
        return self._notes

    @property
    def degree(self) -> int:
        return self._degree

    @property
    def pattern(self) -> str:
        return self._pattern


class Drums:
    def __init__(self, main_pattern: str | None = None, bridge_pattern: str | None = None):
        if (main_pattern is None and bridge_pattern is not None or
                main_pattern is not None and bridge_pattern is None):
            raise ValueError(f"Both main_pattern and bridge_pattern have to have a pattern, or both None.")

        if main_pattern and main_pattern not in DRUM_MAIN_PATTERNS:  # STRAIGHT, ROCK, SYNCOPATED (and None too)
            raise ValueError(f"Invalid main drum pattern: {main_pattern}. Can only choose from {DRUM_MAIN_PATTERNS}.")
        self._main_pattern = main_pattern

        if bridge_pattern and bridge_pattern not in DRUM_BRIDGE_PATTERNS:  # STRAIGHT, HALF-TIME, SPARSE (and None)
            raise ValueError(f"""Invalid bridge drum pattern: {bridge_pattern}.
                            Can only choose from {DRUM_BRIDGE_PATTERNS}.""")
        self._bridge_pattern = bridge_pattern

    def __repr__(self):
        """string representation"""
        return f"""Drums(
            main_pattern={self._main_pattern},
            bridge_pattern={self._bridge_pattern} \n
        )"""

    @property
    def main_pattern(self) -> str:
        return self._main_pattern

    @property
    def bridge_pattern(self) -> str:
        return self._bridge_pattern

    def is_empty(self) -> bool:
        """As a drums object can exist without it being used, this function return if it's used or not."""
        return not self._main_pattern and not self._bridge_pattern


class Song:
    def __init__(self, chords: list[Chord], melody: list[Note], drums: Drums, tempo: int,
                 instruments: dict[str, str], beats: dict[str, int]):
        if not chords:
            raise ValueError(f"Invalid chord structure. Has to contain at least one chord.")
        self._chords = chords

        if not melody:
            raise ValueError(f"Invalid melody. Has to contain at least one note.")
        self._melody = melody

        if drums is None:  # it could still have all NONE variables
            raise ValueError(f"Invalid drums. Have to contain something.")
        self._drums = drums

        if tempo < 1:
            raise ValueError(f"Invalid tempo: {tempo}. Can only be a natural number.")
        self._tempo = tempo

        if (not instruments or len(instruments) != 2 or  # CHORDS: , MELODY:
                "CHORDS" not in instruments.keys() or "MELODY" not in instruments.keys()):
            raise ValueError(f"Invalid instruments: {instruments}. Have to have 2 instruments CHORDS, MELODY.")
        self._instruments = instruments

        if not beats or list(beats.keys()) != SONG_PARTS: # INTRO: , VERSE: , BRIDGE: , CHORUS: , ENDING:
            raise ValueError(f"Invalid beats: {beats}. Have to have 5 parts INTRO, VERSE, BRIDGE, CHORUS, ENDING.")
        self._beats = beats

    def __repr__(self):
        """string representation"""
        return f"""Song(
            chords={self._chords},
            melody={self._melody},
            drums={self._drums},
            tempo={self._tempo},
            instruments: {self._instruments["CHORDS"]} on chords, {self._instruments["MELODY"]} on melody,
            Length in beats: {self._beats} \n
        )"""

    @property
    def chords(self) -> list[Chord]:
        return self._chords

    @property
    def melody(self) -> list[Note]:
        return self._melody

    @property
    def drums(self) -> Drums:
        return self._drums

    @property
    def tempo(self) -> int:
        return self._tempo

    @property
    def instruments(self) -> dict[str, str]:
        return self._instruments

    @property
    def beats(self) -> dict[str, int]:
        return self._beats

    @cached_property
    def sum_of_beats(self) -> int:
        """returns the sum of all length (in beats)."""
        return sum(self._beats.values())
