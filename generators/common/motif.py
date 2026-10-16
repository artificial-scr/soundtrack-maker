"""Motifs as relative scale-index shapes: load human-written themes and transform them."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from .theory import Key


@dataclass(frozen=True)
class Motif:
    """Scale-index offsets from the first note, with durations in beats. Rests have offset None."""

    offsets: tuple[int | None, ...]
    durations: tuple[float, ...]
    source: str = "generated"

    def __post_init__(self) -> None:
        if len(self.offsets) != len(self.durations):
            raise ValueError("offsets and durations must have the same length")

    @property
    def length(self) -> float:
        return sum(self.durations)

    @property
    def steps(self) -> list[int]:
        """Interval steps between consecutive sounding notes (Markov training data)."""
        sounding = [o for o in self.offsets if o is not None]
        return [b - a for a, b in zip(sounding, sounding[1:])]

    def transpose(self, steps: int) -> "Motif":
        return replace(self, offsets=tuple(None if o is None else o + steps for o in self.offsets))

    def invert(self) -> "Motif":
        return replace(self, offsets=tuple(None if o is None else -o for o in self.offsets))

    def augment(self, factor: float) -> "Motif":
        return replace(self, durations=tuple(d * factor for d in self.durations))

    def retrograde(self) -> "Motif":
        return replace(self, offsets=self.offsets[::-1], durations=self.durations[::-1])


def load_motif(path: Path, key: Key) -> Motif:
    """Load a MIDI or ABC file with music21 and express it as scale offsets in `key`.

    Chromatic notes are snapped to the nearest scale tone (the pipeline is diatonic for now).
    """
    import music21  # heavy import, only needed when real motifs are used

    score = music21.converter.parse(str(path))
    offsets: list[int | None] = []
    durations: list[float] = []
    first: int | None = None
    for el in score.flatten().notesAndRests:
        dur = float(el.quarterLength)
        if dur <= 0:
            continue
        if el.isRest:
            offsets.append(None)
        else:
            pitch = el.pitches[-1].midi  # top note of a chord
            idx = key.nearest_index(pitch)
            first = idx if first is None else first
            offsets.append(idx - first)
        durations.append(dur)
    if first is None:
        raise ValueError(f"{path} contains no notes")
    return Motif(tuple(offsets), tuple(durations), source=str(path))
