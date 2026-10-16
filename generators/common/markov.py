"""Second-order Markov model over scale-index steps, plus a chord-aware melody writer."""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from .rng import weighted_choice
from .theory import Chord, Key

# Fallback when no motifs are available: mostly steps, some thirds, rare larger leaps.
DEFAULT_STEP_PRIOR = {0: 0.5, 1: 3.0, -1: 3.2, 2: 1.4, -2: 1.5, 3: 0.5, -3: 0.5, 4: 0.3, -4: 0.35}
TRAINING_WEIGHT = 6.0

# A rhythm cell is a sequence of (duration in beats, is_rest).
Cell = tuple[tuple[float, bool], ...]


class StepMarkov:
    def __init__(self, order: int = 2, training: Iterable[Sequence[int]] = (), prior: dict[int, float] | None = None):
        self.order = order
        self.prior = dict(DEFAULT_STEP_PRIOR if prior is None else prior)
        self.counts: dict[tuple[int, ...], Counter] = defaultdict(Counter)
        for seq in training:
            seq = list(seq)
            for i in range(len(seq)):
                for k in range(1, order + 1):
                    if i - k >= 0:
                        self.counts[tuple(seq[i - k : i])][seq[i]] += 1

    def weights(self, history: Sequence[int]) -> dict[int, float]:
        w = dict(self.prior)
        for k in range(min(self.order, len(history)), 0, -1):
            ctx = tuple(history[-k:])
            if ctx in self.counts:
                total = sum(self.counts[ctx].values())
                for step, c in self.counts[ctx].items():
                    w[step] = w.get(step, 0.0) + TRAINING_WEIGHT * c / total
                break
        return w


@dataclass
class MelodyNote:
    beat: float  # absolute beat position
    duration: float  # beats
    index: int  # scale index


def choose_cells(rng: random.Random, cells: Sequence[Cell], weights: Sequence[float], length: float) -> list[tuple[float, bool]]:
    """Fill `length` beats with rhythm cells, truncating the last one if needed."""
    out: list[tuple[float, bool]] = []
    filled = 0.0
    while filled < length - 1e-9:
        cell = weighted_choice(rng, list(cells), list(weights))
        for dur, rest in cell:
            dur = min(dur, length - filled)
            if dur <= 1e-9:
                break
            out.append((dur, rest))
            filled += dur
    return out


def write_melody(
    rng: random.Random,
    markov: StepMarkov,
    key: Key,
    chord_at: Callable[[float], Chord],
    rhythm: Sequence[tuple[float, bool]],
    start_beat: float,
    start_index: int,
    lo_index: int,
    hi_index: int,
    history: list[int] | None = None,
    land_on_chord_tone: bool = True,
) -> tuple[list[MelodyNote], int, list[int]]:
    """Walk the Markov chain over a rhythm, biased toward chord tones on strong beats.

    Returns (notes, last scale index, step history) so phrases can be chained.
    """
    history = list(history or [])
    notes: list[MelodyNote] = []
    idx = start_index
    beat = start_beat
    center = (lo_index + hi_index) / 2
    span = max(1, hi_index - lo_index)
    sounding = [i for i, (_, rest) in enumerate(rhythm) if not rest]
    last_sounding = sounding[-1] if sounding else -1

    for i, (dur, rest) in enumerate(rhythm):
        if rest:
            beat += dur
            continue
        chord = chord_at(beat)
        strong = abs(beat - round(beat)) < 1e-9 and int(round(beat)) % 2 == 0
        final = land_on_chord_tone and i == last_sounding

        steps, weights = [], []
        for step, w in sorted(markov.weights(history).items()):
            cand = idx + step
            if not lo_index <= cand <= hi_index:
                continue
            in_chord = chord.contains(key.pitch(cand))
            if final:
                w *= 12.0 if in_chord else 0.05
            elif strong:
                w *= 4.0 if in_chord else 0.35
            elif in_chord:
                w *= 1.4
            # After a leap, prefer to step back the other way.
            if history and abs(history[-1]) >= 3 and step * history[-1] > 0:
                w *= 0.15
            # Avoid hammering the same note.
            if step == 0 and history and history[-1] == 0:
                w *= 0.2
            # Gentle pull toward the middle of the range.
            w *= math.exp(-2.0 * ((cand - center) / span) ** 2)
            if w > 0:
                steps.append(step)
                weights.append(w)
        if not steps:  # out of range: jump to the nearest chord tone
            options = [c for c in range(lo_index, hi_index + 1) if chord.contains(key.pitch(c))]
            target = min(options, key=lambda c: (abs(c - idx), c))
            steps, weights = [target - idx], [1.0]

        step = weighted_choice(rng, steps, weights)
        idx += step
        history.append(step)
        notes.append(MelodyNote(beat, dur, idx))
        beat += dur
    return notes, idx, history
