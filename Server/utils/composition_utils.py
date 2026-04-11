# triads, steps between each note in the scale and allowed_next jumps
# in steps, the last step is to wrap back to the start.
SCALE_NAMES = ["MAJOR", "MINOR", "MIXOLYDIAN"]

SCALES = {
    "MAJOR": {
        "TRIADS": [
            [1, 3, 5],  # I
            [2, 4, 6],  # ii
            [3, 5, 7],  # iii
            [4, 6, 1],  # IV
            [5, 7, 2],  # V
            [6, 1, 3],  # vi
            [7, 2, 4]  # vii°
        ],

        "STEPS": [
            2, 2, 1, 2, 2, 2, 1
        ],

        "ALLOWED_NEXT": [
            [1, 2, 4, 5, 6],  # I   → I ii IV V vi
            [5, 7]  ,  # ii  → V vii°
            [4, 6],  # iii → IV vi
            [1, 2, 5, 7],  # IV  → I ii V vii°
            [1, 6],  # V   → I vi
            [2, 4, 5],  # vi  → ii IV V
            [1]  # vii°→ I
        ]
    },

    "MINOR": {
        "TRIADS": [
            [1, 3, 5],  # i
            [2, 4, 6],  # ii°
            [3, 5, 7],  # III
            [4, 6, 1],  # iv
            [5, 7, 2],  # v
            [6, 1, 3],  # VI
            [7, 2, 4]  # VII
        ],

        "STEPS": [
            2, 1, 2, 2, 1, 2, 2
        ],

        "ALLOWED_NEXT": [
            [3, 4, 5, 6, 7],  # i    → III iv v VI VII
            [5, 7, 4],  # ii°  → v VII iv
            [6, 7, 4],  # III  → VI VII iv
            [1, 5, 7, 2],  # iv   → i v VII ii°
            [1, 6, 7, 4],  # v    → i VI VII iv
            [3, 7, 2, 4],  # VI   → III VII ii° iv
            [1, 3, 6],  # VII  → i III VI
        ]
    },

    "MIXOLYDIAN": {
        "TRIADS": [
            [1, 3, 5],  # I
            [2, 4, 6],  # ii
            [3, 5, 7],  # iii°
            [4, 6, 1],  # IV
            [5, 7, 2],  # v
            [6, 1, 3],  # vi
            [7, 2, 4]  # VII
        ],

        "STEPS": [
            2, 2, 1, 2, 2, 1, 2
        ],

        "ALLOWED_NEXT": [
            [2, 4, 5, 6, 7],  # I    → ii IV v vi VII
            [5, 7, 4],  # ii   → v VII IV
            [4, 6, 7],  # iii° → IV vi VII
            [1, 5, 7, 2],  # IV   → I v VII ii
            [1, 4, 7, 6],  # v    → I IV VII vi
            [2, 4, 5, 7],  # vi   → ii IV v VII
            [1, 4, 6],  # VII  → I IV vi
        ]
    }
}

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]  # 12 notes in an octave


def note_to_pitch(note_name: str) -> int:
    """Convert note name to pitch number (0-11)."""
    return NOTES.index(note_name)


def get_beat_position(beats: float) -> int:
    """returns the position of the beat (1-4) inside the bar."""
    return (int(beats % 4)) + 1  # +1 because we return it as 1-indexed


BEATS_PER_BAR = 4  # always 4/4
NOTE_VELOCITIES = [60, 70, 80, 90, 100, 110, 120]
NOTE_BEATS = [0.5, 1.0, 1.5, 2.0, 4.0]
VERSE_CHORUS_BARS = [4, 8, 12, 16]
COMPLEXITIES = ["SIMPLE", "MEDIUM", "COMPLEX"]
SONG_PARTS = ["INTRO", "VERSE", "BRIDGE", "CHORUS", "ENDING"]
PATTERNS = ["SUSTAINED 1", "SUSTAINED 2", "SUSTAINED 4", "ARPEGGIO UP", "ARPEGGIO DOWN",
            "OFFBEAT", "WALTZ-LIKE", "STRIDE"]
OCTAVES = [3, 4, 5, 6]
ARPEGGIO_OCTAVES = [2, 3, 4, 5] # these are a little lower
CHORD_OCTAVES = { # arpeggio octaves aren't here as they're assigned differently
    "SUSTAINED": [3, 3, 3],  # root -> 3rd -> 5th
    "OFFBEAT": [3, 3, 3],  # root -> 3rd -> 5th
    "WALTZ-LIKE": [3, 3, 3],  # root -> 3rd -> 5th
    "STRIDE": [3, 3, 3]  # root -> 3rd -> 5th
}
INSTRUMENTS = ["PIANO", "NYLON GUITAR", "ROCK GUITAR", "SYNTH"]
INSTRUMENTS_MIDI_CHANNELS = {
    "PIANO": 0,
    "NYLON GUITAR": 24,
    "ROCK GUITAR": 29,
    "SYNTH": 90
}

# drums
DRUM_MAIN_PATTERNS = ["STRAIGHT", "ROCK", "SYNCOPATED"]
DRUM_BRIDGE_PATTERNS = ["STRAIGHT", "HALF-TIME", "SPARSE"]
MIDI_DRUM_PITCHES = {
    "KICK": 36,
    "SNARE": 38,
    "CLOSED HI-HAT": 42,
    "CRASH": 49,
    "HIGH TOM": 48,
}
DRUM_VELOCITIES = {
    "KICK": 85,
    "SNARE": 95,
    "CLOSED HI-HAT": 70,
    "CRASH": 105,
    "HIGH TOM": 90
}
STRAIGHT_DRUM_PATTERN = {
    "MAIN": [
        ["KICK", "CLOSED HI-HAT"],  # 1
        ["CLOSED HI-HAT"],  # &
        ["SNARE", "CLOSED HI-HAT"],  # 2
        ["CLOSED HI-HAT"],  # &
        ["KICK", "CLOSED HI-HAT"],  # 3
        ["CLOSED HI-HAT"],  # &
        ["SNARE", "CLOSED HI-HAT"],  # 4
        ["CLOSED HI-HAT"]  # &
    ],
    "FILL": [
        ["SNARE"],
        ["SNARE"],
        ["SNARE", "HIGH TOM"],
        ["KICK", "CRASH"],
    ]
}

ROCK_DRUM_PATTERN = {
    "MAIN": [
        ["KICK", "CLOSED HI-HAT"],  # 1
        ["KICK", "CLOSED HI-HAT"],  # &
        ["SNARE", "CLOSED HI-HAT"],  # 2
        ["KICK", "CLOSED HI-HAT"],  # &
        ["KICK", "CLOSED HI-HAT"],  # 3
        ["KICK", "CLOSED HI-HAT"],  # &
        ["SNARE", "CLOSED HI-HAT"],  # 4
        ["CLOSED HI-HAT"]  # &
    ],
    "FILL": [
        ["SNARE"],
        ["SNARE", "HIGH TOM"],
        ["HIGH TOM"],
        ["KICK", "CRASH"],
    ]
}

HALF_TIME_DRUM_PATTERN = {
    "MAIN": [
        ["KICK", "CLOSED HI-HAT"],  # 1
        [],  # &
        ["CLOSED HI-HAT"],  # 2
        [],  # &
        ["SNARE", "CLOSED HI-HAT"],  # 3
        [],  # &
        ["CLOSED HI-HAT"],  # 4
        [],  # &
    ],
    "FILL": [
        [],
        ["SNARE"],
        ["HIGH TOM"],
        ["KICK", "CRASH"],
    ]
}

SYNCOPATED_DRUM_PATTERN = {
    "MAIN": [
        ["KICK", "CLOSED HI-HAT"],  # 1
        ["CLOSED HI-HAT"],  # &
        ["SNARE", "CLOSED HI-HAT"],  # 2
        ["KICK", "CLOSED HI-HAT"],  # &
        ["CLOSED HI-HAT"],  # 3
        ["KICK", "CLOSED HI-HAT"],  # &
        ["SNARE", "CLOSED HI-HAT"],  # 4
        ["CLOSED HI-HAT"]  # &
    ],
    "FILL": [
        ["SNARE"],
        ["SNARE", "HIGH TOM"],
        ["KICK"],
        ["KICK", "CRASH"],
    ]
}

SPARSE_DRUM_PATTERN = {
    "MAIN": [
        ["KICK"],  # 1
        [],  # &
        ["SNARE"],  # 2
        [],  # &
        ["KICK"],  # 3
        [],  # &
        ["SNARE"],  # 4
        []  # &
    ],
    "FILL": [
        [],
        ["SNARE"],
        ["HIGH TOM"],
        ["KICK", "CRASH"],
    ]
}
DRUM_TO_PATTERN_MAP = {
    "STRAIGHT": (STRAIGHT_DRUM_PATTERN, {"VERSE", "BRIDGE", "CHORUS"}),
    "ROCK": (ROCK_DRUM_PATTERN, {"VERSE", "CHORUS"}),
    "SYNCOPATED": (SYNCOPATED_DRUM_PATTERN, {"VERSE", "CHORUS"}),
    "HALF-TIME": (HALF_TIME_DRUM_PATTERN, {"BRIDGE"}),
    "SPARSE": (SPARSE_DRUM_PATTERN, {"BRIDGE"}),
}
# weights / shifts related, or used for calculation in composer.py...
BASE_CHORD_PATTERN_WEIGHTS = {
    "SUSTAINED 1": 0.14,
    "SUSTAINED 2": 0.14,
    "SUSTAINED 4": 0.15,
    "ARPEGGIO UP": 0.12,
    "ARPEGGIO DOWN": 0.12,
    "WALTZ-LIKE": 0.12,
    "STRIDE": 0.11,
    "OFFBEAT": 0.10
}

# big lookup table for _get_chord_pattern...
CHORD_PATTERN_MULTIPLIERS = {
    "complexity": {
        "SIMPLE": {
            "SUSTAINED 1": 1.8, "SUSTAINED 2": 1.5, "SUSTAINED 4": 0.8,
            "ARPEGGIO UP": 0.5, "ARPEGGIO DOWN": 0.5, "STRIDE": 0.1, "OFFBEAT": 0.0,
        },
        "COMPLEX": {
            "ARPEGGIO UP": 1.6, "ARPEGGIO DOWN": 1.6, "STRIDE": 1.5, "OFFBEAT": 1.5,
            "WALTZ-LIKE": 1.4, "SUSTAINED 2": 0.1, "SUSTAINED 1": 0.0,
        },
    },
    "instrument": {
        "PIANO": {"STRIDE": 1.5, "ARPEGGIO UP": 1.4, "ARPEGGIO DOWN": 1.4, "WALTZ-LIKE": 1.3},
        "NYLON GUITAR": {"SUSTAINED 2": 1.3, "SUSTAINED 1": 1.1, "STRIDE": 0.2},
        "ROCK GUITAR": {"SUSTAINED 4": 1.5, "SUSTAINED 2": 1.2, "OFFBEAT": 1.1,
                        "ARPEGGIO UP": 0.6, "ARPEGGIO DOWN": 0.6, "STRIDE": 0.2},
        "SYNTH": {"OFFBEAT": 1.3, "SUSTAINED 1": 1.3, "ARPEGGIO UP": 1.2,
                  "WALTZ-LIKE": 0.3, "STRIDE": 0.2},
    },
    "scale": {
        "MAJOR": {"SUSTAINED 1": 1.2, "SUSTAINED 2": 1.2, "ARPEGGIO UP": 1.1},
        "MINOR": {"ARPEGGIO DOWN": 1.3, "ARPEGGIO UP": 1.2, "SUSTAINED 1": 1.1, "STRIDE": 0.7},
        "MIXOLYDIAN": {"OFFBEAT": 1.3, "STRIDE": 1.2, "SUSTAINED 4": 0.8},
    },
    "tempo": {
        "slow": {"ARPEGGIO UP": 1.2, "ARPEGGIO DOWN": 1.2, "SUSTAINED 2": 1.2, "SUSTAINED 1": 0.8},
        "fast": {"SUSTAINED 2": 1.2, "SUSTAINED 4": 1.2, "OFFBEAT": 1.2,
                 "ARPEGGIO UP": 0.7, "ARPEGGIO DOWN": 0.7},
    },
    "drums": {
        True: {"SUSTAINED 1": 1.2, "SUSTAINED 2": 1.2, "OFFBEAT": 0.7},
        False: {"OFFBEAT": 1.2, "WALTZ-LIKE": 1.2},
    },
    "song_part": {
        "INTRO": {"SUSTAINED 1": 1.1, "OFFBEAT": 0.8},
        "CHORUS": {"OFFBEAT": 1.1},
        "BRIDGE": {"ARPEGGIO UP": 1.1, "ARPEGGIO DOWN": 1.1, "WALTZ-LIKE": 1.1, "SUSTAINED 1": 0.8},
    },
}

BASE_NOTE_VELOCITY_WEIGHTS = {
    60: 0.08,
    70: 0.14,
    80: 0.20,
    90: 0.26,
    100: 0.18,
    110: 0.10,
    120: 0.04,
}

VELOCITY_DEGREE_SHIFTS = {
    "MAJOR": {1: -0.1, 2: 0.1, 3: 0.0, 4: 0.15, 5: 0.3, 6: -0.1, 7: 0.25},
    "MINOR": {1: -0.1, 2: 0.2, 3: -0.1, 4: 0.15, 5: 0.15, 6: -0.05, 7: -0.1},
    "MIXOLYDIAN": {1: -0.1, 2: 0.1, 3: 0.0, 4: 0.15, 5: 0.1, 6: -0.1, 7: -0.15},
}

VELOCITY_BEAT_SHIFTS = {1: 0.4, 2: -0.3, 3: 0.1, 4: -0.3}

BASE_NOTE_BEATS_WEIGHTS = {
    0.5: 0.35,
    1.0: 0.35,
    1.5: 0.05,
    2.0: 0.15,
    4.0: 0.10,
}
