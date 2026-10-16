"""Keys, modes, diatonic chords and scale-index arithmetic."""

from __future__ import annotations

from dataclasses import dataclass

NOTE_PCS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

MODES = {
    "ionian": (0, 2, 4, 5, 7, 9, 11),
    "major": (0, 2, 4, 5, 7, 9, 11),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "lydian": (0, 2, 4, 6, 7, 9, 11),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "aeolian": (0, 2, 3, 5, 7, 8, 10),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "locrian": (0, 1, 3, 5, 6, 8, 10),
}

ROMAN = {"i": 0, "ii": 1, "iii": 2, "iv": 3, "v": 4, "vi": 5, "vii": 6}


def parse_pc(name: str) -> int:
    name = name.strip()
    pc = NOTE_PCS[name[0].upper()]
    for accidental in name[1:]:
        pc += {"#": 1, "b": -1}[accidental]
    return pc % 12


@dataclass(frozen=True)
class Key:
    tonic: int  # pitch class 0..11
    mode: str
    tonic_name: str

    @classmethod
    def parse(cls, text: str) -> "Key":
        """Parse e.g. "D dorian" or "F# minor"."""
        parts = text.split()
        if len(parts) != 2 or parts[1].lower() not in MODES:
            raise ValueError(f"key must look like 'D dorian', got {text!r}")
        return cls(parse_pc(parts[0]), parts[1].lower(), parts[0])

    def __str__(self) -> str:
        return f"{self.tonic_name} {self.mode}"

    @property
    def intervals(self) -> tuple[int, ...]:
        return MODES[self.mode]

    @property
    def pitch_classes(self) -> tuple[int, ...]:
        return tuple((self.tonic + i) % 12 for i in self.intervals)

    # Scale index: 0 is the tonic at MIDI octave 0 (C-1 region); +7 is one octave up.
    def pitch(self, index: int) -> int:
        octave, degree = divmod(index, 7)
        return 12 * octave + self.tonic + self.intervals[degree]

    def index_of(self, pitch: int) -> int:
        """Scale index of a diatonic MIDI pitch. Raises if the pitch is not in the key."""
        rel = pitch - self.tonic
        octave, semis = divmod(rel, 12)
        if semis not in self.intervals:
            raise ValueError(f"pitch {pitch} is not in {self}")
        return 7 * octave + self.intervals.index(semis)

    def nearest_index(self, pitch: int) -> int:
        for delta in (0, -1, 1, -2, 2):
            try:
                return self.index_of(pitch + delta)
            except ValueError:
                continue
        raise AssertionError("unreachable: every semitone is within 1 of a scale note")

    def indices_in_range(self, lo: int, hi: int) -> list[int]:
        """All scale indices whose pitch lies within [lo, hi] (MIDI numbers)."""
        start = self.nearest_index(lo)
        while self.pitch(start) < lo:
            start += 1
        out = []
        i = start
        while self.pitch(i) <= hi:
            out.append(i)
            i += 1
        return out

    def chord(self, roman: str, size: int = 3) -> "Chord":
        degree = ROMAN[roman.lower()]
        degrees = tuple(degree + 2 * k for k in range(size))
        return Chord(roman, degree, tuple(self.pitch(d) % 12 for d in degrees))


@dataclass(frozen=True)
class Chord:
    roman: str
    degree: int  # scale degree of the root, 0..6
    pcs: tuple[int, ...]  # root, third, fifth (, seventh)

    @property
    def root_pc(self) -> int:
        return self.pcs[0]

    def contains(self, pitch: int) -> bool:
        return pitch % 12 in self.pcs


def lowest_pitch_with_pc(pc: int, lo: int, hi: int) -> int:
    for p in range(lo, hi + 1):
        if p % 12 == pc:
            return p
    raise ValueError(f"no pitch class {pc} between {lo} and {hi}")
