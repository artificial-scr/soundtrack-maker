"""Data-driven arranger shared by the level generators.

A level module declares a `LevelSpec`: key, chord progressions and, per cue, a palette of
alternative recipes for each stem. A seed picks one progression (shared by all cues, as is
the motif germ) and, per cue, one recipe per stem plus the options inside it. That is where
seed-to-seed variety comes from.

Option values given as a **list** are choices (the seed picks one); tuples are literal values.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable

from .grid import Grid
from .markov import Cell, MelodyNote, StepMarkov, choose_cells, write_melody
from .motif import Motif
from .rng import sub_rng, weighted_choice
from .stems import Arrangement, Part
from .theory import Chord, Key, lowest_pitch_with_pc

STEMS = ["pads", "bass", "percussion", "lead", "danger"]
PHRASE_BARS = 4
F, R = False, True  # rhythm-cell flags: sounding / rest

# ---------------------------------------------------------------- spec types


@dataclass(frozen=True)
class PartSpec:
    writer: str
    program: int
    lo: int
    hi: int
    vel: int = 80
    volume: int = 100
    pan: int = 64
    name: str = ""
    opts: dict = field(default_factory=dict, hash=False, compare=False)


def P(writer: str, program: int, lo: int, hi: int, vel: int = 80, volume: int = 100, pan: int = 64,
      name: str = "", **opts) -> PartSpec:
    return PartSpec(writer, program, lo, hi, vel, volume, pan, name, opts)


@dataclass(frozen=True)
class DrumVoice:
    note: int
    patterns: tuple[tuple[float, ...], ...]  # onset beats within a bar; the seed picks one
    vel: int = 70
    prob: float = 1.0  # chance each hit sounds
    accent: int = 8  # extra velocity on the downbeat
    alt: float = 0.15  # chance per bar of swapping to another pattern


def V(note: int, *patterns: tuple[float, ...], vel: int = 70, prob: float = 1.0, accent: int = 8, alt: float = 0.15) -> DrumVoice:
    return DrumVoice(note, tuple(patterns), vel, prob, accent, alt)


@dataclass(frozen=True)
class DrumSpec:
    voices: tuple[DrumVoice, ...]
    fills: tuple[tuple[tuple[float, int], ...], ...] = ()  # played in the last bar of each phrase
    crash: int = 0  # cymbal note on phrase starts (0 = none)
    kit: int = 0  # GM/GS drum kit program (0 standard, 8 room, 16 power, 24 electronic, 25 808, 32 jazz, 40 brush, 48 orchestral)
    volume: int = 100


def Kit(*voices: DrumVoice, fills=(), crash: int = 0, kit: int = 0, volume: int = 100) -> DrumSpec:
    return DrumSpec(tuple(voices), tuple(fills), crash, kit, volume)


@dataclass(frozen=True)
class CueSpec:
    bpm: int
    pads: list  # alternatives: PartSpec or tuple[PartSpec, ...]
    bass: list
    percussion: list[DrumSpec]
    lead: list
    danger: list


@dataclass(frozen=True)
class LevelSpec:
    area: str
    key: str
    progressions: list[tuple[str, ...]]  # one roman numeral per bar, length divides `bars`
    cues: dict[str, CueSpec]
    bars: int = 16
    fx: dict = field(default_factory=dict, hash=False, compare=False)  # per-stem overrides of render.master.STEM_FX
    description: str = ""


# ---------------------------------------------------------------- shared libraries

QUARTERS = (0, 1, 2, 3)
OFFBEATS = (0.5, 1.5, 2.5, 3.5)
EIGHTHS = tuple(i * 0.5 for i in range(8))
SIXTEENTHS = tuple(i * 0.25 for i in range(16))

FILLS = {
    "snare16": tuple((2 + i * 0.25, 38) for i in range(8)),
    "toms": ((2, 50), (2.25, 50), (2.5, 48), (2.75, 48), (3, 47), (3.25, 47), (3.5, 45), (3.75, 45)),
    "mixed": ((2, 38), (2.5, 38), (2.75, 38), (3, 38), (3.25, 50), (3.5, 47), (3.75, 45)),
    "half": ((3, 38), (3.25, 38), (3.5, 38), (3.75, 38)),
    "toms_low": ((3, 47), (3.25, 45), (3.5, 43), (3.75, 41)),
}

CELLS: dict[str, tuple[list[Cell], list[float]]] = {
    "long": ([((4, F),), ((2, F), (2, F)), ((3, F), (1, F)), ((2, F), (2, R))], [2, 3, 2, 1.5]),
    "sparse": ([((2, F),), ((1, F), (1, F)), ((1.5, F), (0.5, F)), ((1, F), (1, R)), ((0.5, F), (0.5, F), (1, F))], [2, 3, 2, 1.5, 1]),
    "medium": ([((1, F), (1, F)), ((1.5, F), (0.5, F)), ((0.5, F), (0.5, F), (1, F)), ((1, F), (0.5, F), (0.5, F)), ((2, F),)], [3, 2, 2, 2, 1]),
    "flowing": ([((0.5, F),) * 4, ((0.5, F), (0.5, F), (1, F)), ((1, F), (0.5, F), (0.5, F)), ((0.75, F), (0.25, F), (1, F))], [3, 2, 2, 1]),
    "busy": ([((0.5, F),) * 4, ((0.75, F), (0.75, F), (0.5, F)), ((0.5, F), (0.5, F), (1, F)), ((1, F), (0.5, F), (0.5, F)),
              ((0.25, F), (0.25, F), (0.5, F), (1, F)), ((1.5, F), (0.5, F))], [3, 2, 2.5, 2, 1, 1]),
}

GERM_CELLS: list[Cell] = [
    ((1, F), (1, F), (2, F)),
    ((1.5, F), (0.5, F), (1, F), (1, F)),
    ((0.5, F), (0.5, F), (1, F), (2, F)),
    ((1, F), (0.5, F), (0.5, F), (2, F)),
    ((2, F), (1, F), (1, F)),
    ((1, F), (1, F), (1, F), (1, F)),
    ((0.5, F), (0.5, F), (0.5, F), (0.5, F), (2, F)),
    ((1.5, F), (1.5, F), (1, F)),
]
GERM_WEIGHTS = [3, 2, 2, 2, 1.5, 1, 1.5, 1.5]


# ---------------------------------------------------------------- context


@dataclass
class Ctx:
    area: str
    cue: str
    seed: int
    key: Key
    grid: Grid
    romans: list[str]
    germ: Motif
    markov: StepMarkov

    def __post_init__(self) -> None:
        self.chords = [self.key.chord(r) for r in self.romans]

    @property
    def bpb(self) -> int:
        return self.grid.beats_per_bar

    @property
    def phrases(self) -> int:
        return self.grid.bars // PHRASE_BARS

    def chord(self, bar: int) -> Chord:
        return self.chords[bar % self.grid.bars]

    def chord_at(self, beat: float) -> Chord:
        return self.chord(int(beat // self.bpb))

    def t(self, bar: int, beat: float = 0.0) -> int:
        return self.grid.beat_ticks(bar * self.bpb + beat)

    def beats(self, b: float) -> int:
        return round(b * self.grid.ppq)


def resolve(opts: dict, rng: random.Random) -> dict:
    return {k: (rng.choice(v) if isinstance(v, list) else v) for k, v in opts.items()}


def vel(rng: random.Random, base: int, jitter: int = 5) -> int:
    return base + rng.randint(-jitter, jitter)


def fold(pitch: int, lo: int, hi: int) -> int:
    """Move a pitch by octaves into [lo, hi]."""
    while pitch < lo:
        pitch += 12
    while pitch > hi:
        pitch -= 12
    if pitch < lo:
        raise ValueError(f"range {lo}-{hi} is narrower than an octave")
    return pitch


def new_part(s: PartSpec, default_name: str, mono: bool = False) -> Part:
    return Part(s.name or default_name, program=s.program, lo=s.lo, hi=s.hi, monophonic=mono, pan=s.pan, volume=s.volume)


def voicing(chord: Chord, lo: int, hi: int, prev: tuple[int, ...] | None, size: int = 3) -> tuple[int, ...]:
    """Close-position voicing inside [lo, hi], voice-led from `prev` (smallest total motion)."""
    candidates = []
    for bass in range(lo, hi + 1):
        if bass % 12 not in chord.pcs:
            continue
        k = chord.pcs.index(bass % 12)
        v = [bass]
        for j in range(1, size):
            pc = chord.pcs[(k + j) % len(chord.pcs)]
            nxt = v[-1] + 1
            while nxt % 12 != pc:
                nxt += 1
            v.append(nxt)
        if v[-1] <= hi:
            candidates.append(tuple(v))
    if not candidates:
        raise ValueError(f"no {size}-note voicing of {chord.roman} fits {lo}-{hi}")
    if prev is None or len(prev) != size:
        mid = (lo + hi) / 2
        return min(candidates, key=lambda v: (abs(sum(v) / len(v) - mid), v))
    return min(candidates, key=lambda v: (sum(abs(a - b) for a, b in zip(v, prev)), v))


def chord_tones_in(chord: Chord, lo: int, hi: int) -> list[int]:
    return [p for p in range(lo, hi + 1) if chord.contains(p)]


def swell_controls(part: Part, ctx: Ctx, cycle_beats: float, low: int = 55, high: int = 127, phase: float = 0.0) -> None:
    """CC11 expression swell repeating every `cycle_beats` (must divide the loop)."""
    total = ctx.grid.total_beats
    if abs(total / cycle_beats - round(total / cycle_beats)) > 1e-9:
        raise ValueError(f"swell cycle {cycle_beats} beats does not divide the {total}-beat loop")
    step = 0.25
    for i in range(int(total / step)):
        b = i * step
        x = ((b / cycle_beats) + phase) % 1.0
        value = low + (high - low) * (0.5 - 0.5 * math.cos(2 * math.pi * x))
        part.cc(ctx.grid.beat_ticks(b), 11, int(round(value)))


# ---------------------------------------------------------------- harmony writers


def w_sustain(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Held chords, one voicing per bar. opts: size, split (chance of re-voicing mid-bar), swell (beats)."""
    part = new_part(s, "pad")
    size = o.get("size", 3)
    prev = None
    for bar in range(ctx.grid.bars):
        chord = ctx.chord(bar)
        prev = voicing(chord, s.lo, s.hi, prev, size)
        if rng.random() < o.get("split", 0.0):
            half = ctx.bpb / 2
            for p in prev:
                part.add(ctx.t(bar), ctx.beats(half), p, vel(rng, s.vel, 4))
            alt = [v for v in _all_voicings(chord, s.lo, s.hi, size) if v != prev] or [prev]
            second = min(alt, key=lambda v: (sum(abs(a - b) for a, b in zip(v, prev)), v))
            for p in second:
                part.add(ctx.t(bar, half), ctx.beats(half), p, vel(rng, s.vel - 4, 4))
            prev = second
        else:
            for p in prev:
                part.add(ctx.t(bar), ctx.beats(ctx.bpb), p, vel(rng, s.vel, 4))
    if o.get("swell"):
        swell_controls(part, ctx, o["swell"], low=o.get("swell_low", 60))
    return [part]


def _all_voicings(chord: Chord, lo: int, hi: int, size: int) -> list[tuple[int, ...]]:
    out = []
    for bass in range(lo, hi + 1):
        if bass % 12 in chord.pcs:
            try:
                v = voicing(chord, bass, hi, None, size)
            except ValueError:
                continue
            if v[0] == bass:
                out.append(v)
    return out


def w_stabs(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Short chords on a rhythm chosen per phrase. opts: rhythms (list of onset tuples), length."""
    part = new_part(s, "stabs")
    rhythms = o.get("rhythms", [(0.5, 1.5, 2.5, 3.5), (0, 1.5, 3), (0, 0.75, 1.5, 2.5, 3)])
    length = o.get("length", 0.4)
    prev = None
    for ph in range(ctx.phrases):
        onsets = rng.choice(rhythms) if isinstance(rhythms, list) else rhythms
        for bar in range(ph * PHRASE_BARS, (ph + 1) * PHRASE_BARS):
            prev = voicing(ctx.chord(bar), s.lo, s.hi, prev, o.get("size", 3))
            for i, on in enumerate(onsets):
                nxt = onsets[i + 1] if i + 1 < len(onsets) else ctx.bpb
                dur = min(length, nxt - on)
                for p in prev:
                    part.add(ctx.t(bar, on), ctx.beats(dur), p, vel(rng, s.vel + (8 if i == 0 else 0), 4))
    return [part]


ARP_SHAPES = {
    "up": lambda n: list(range(n)),
    "down": lambda n: list(range(n))[::-1],
    "updown": lambda n: list(range(n)) + list(range(n - 2, 0, -1)),
    "alberti": lambda n: [0, 2, 1, 2] if n >= 3 else [0, 1],
    "broken": lambda n: [0, 2, 1, 3, 2, 4, 3, 1][: max(4, min(8, n + 3))] if n >= 5 else [0, 2, 1, 2],
    "pendulum": lambda n: [0, n - 1, 1, n - 2] if n >= 4 else [0, 2, 1, 2],
}


def w_arp(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Broken chords. opts: shape, rate (beats per note), span (chord tones), artic."""
    part = new_part(s, "arp")
    rate = o.get("rate", 0.5)
    span = o.get("span", 5)
    artic = o.get("artic", 0.9)
    shape = ARP_SHAPES[o.get("shape", "up")]
    slots = int(round(ctx.bpb / rate))
    prev = None
    for bar in range(ctx.grid.bars):
        chord = ctx.chord(bar)
        base = voicing(chord, s.lo, min(s.hi, s.lo + 14), prev, 3)
        prev = base
        tones = [p for p in chord_tones_in(chord, base[0], s.hi)][:span]
        order = shape(len(tones))
        for i in range(slots):
            p = tones[order[i % len(order)] % len(tones)]
            accent = 8 if i == 0 else (3 if (i * rate) % 1 == 0 else 0)
            part.add(ctx.t(bar, i * rate), ctx.beats(rate * artic), p, vel(rng, s.vel + accent, 4))
    return [part]


def w_pulse(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Repeated chords at a steady rate. opts: rate, artic, accents (beats that get accented)."""
    part = new_part(s, "pulse")
    rate = o.get("rate", 0.5)
    artic = o.get("artic", 0.6)
    accents = o.get("accents", (0, 2))
    prev = None
    for bar in range(ctx.grid.bars):
        prev = voicing(ctx.chord(bar), s.lo, s.hi, prev, o.get("size", 3))
        for i in range(int(round(ctx.bpb / rate))):
            b = i * rate
            for p in prev:
                part.add(ctx.t(bar, b), ctx.beats(rate * artic), p, vel(rng, s.vel + (10 if b in accents else 0), 4))
    return [part]


def w_strum(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Guitar-like strums: chord notes staggered by a few ticks. opts: rhythms, stagger (ticks)."""
    part = new_part(s, "strum")
    rhythms = o.get("rhythms", [(0, 1, 1.5, 2.5, 3), (0, 1.5, 2, 3), (0, 2, 2.5, 3.5)])
    stagger = o.get("stagger", 18)
    prev = None
    for ph in range(ctx.phrases):
        onsets = rng.choice(rhythms) if isinstance(rhythms, list) else rhythms
        for bar in range(ph * PHRASE_BARS, (ph + 1) * PHRASE_BARS):
            prev = voicing(ctx.chord(bar), s.lo, s.hi, prev, o.get("size", 4))
            for i, on in enumerate(onsets):
                nxt = onsets[i + 1] if i + 1 < len(onsets) else ctx.bpb
                down = i % 2 == 0
                notes = prev if down else prev[::-1]
                for j, p in enumerate(notes):
                    start = ctx.t(bar, on) + j * stagger
                    end = ctx.t(bar, nxt) - 10
                    part.add(start, max(30, end - start), p, vel(rng, s.vel + (6 if down else -6), 4))
    return [part]


def w_sparkle(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Sparse random chord-tone glints (crystals, fireflies, bubbles, snow).

    opts: density (chance per slot), rate, figure ("single" | "rise" | "fall" | "twinkle"), length (beats).
    """
    part = new_part(s, "sparkle")
    rate = o.get("rate", 0.5)
    density = o.get("density", 0.2)
    figure = o.get("figure", "single")
    length = o.get("length", 0.5)
    for bar in range(ctx.grid.bars):
        chord = ctx.chord(bar)
        tones = chord_tones_in(chord, s.lo, s.hi)
        for i in range(int(round(ctx.bpb / rate))):
            if rng.random() >= density:
                continue
            b = i * rate
            k = rng.randrange(len(tones))
            if figure == "single":
                seq = [tones[k]]
            elif figure == "rise":
                seq = tones[k : k + 3] if k + 3 <= len(tones) else tones[-3:]
            elif figure == "fall":
                seq = (tones[k : k + 3] if k + 3 <= len(tones) else tones[-3:])[::-1]
            else:  # twinkle: a note and its upper neighbour chord tone
                seq = [tones[k], tones[min(k + 1, len(tones) - 1)]]
            for j, p in enumerate(seq):
                start = b + j * 0.25
                if start + 0.25 > ctx.bpb:
                    break
                part.add(ctx.t(bar, start), ctx.beats(min(length, ctx.bpb - start)), p, vel(rng, s.vel - j * 6, 8))
    return [part]


def w_texture(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """One sustained tonic note per phrase with a slow swell (wind, sea, breath noise)."""
    part = new_part(s, "texture")
    pitch = fold(lowest_pitch_with_pc(ctx.key.tonic, s.lo, s.lo + 11), s.lo, s.hi)
    for ph in range(ctx.phrases):
        part.add(ctx.t(ph * PHRASE_BARS), ctx.beats(PHRASE_BARS * ctx.bpb), pitch, vel(rng, s.vel, 3))
    swell_controls(part, ctx, o.get("swell", PHRASE_BARS * ctx.bpb / 2), low=o.get("swell_low", 30))
    return [part]


# ---------------------------------------------------------------- bass writers

BASS_ROOTS = [
    ((0, "R", 2), (2, "5", 2)),
    ((0, "R", 1.5), (1.5, "R", 0.5), (2, "5", 1), (3, "8", 1)),
    ((0, "R", 3), (3, "APP", 1)),
    ((0, "R", 4),),
    ((0, "R", 1), (1, "5", 1), (2, "8", 1), (3, "5", 1)),
    ((0, "R", 1.5), (1.5, "5", 1), (2.5, "R", 1.5)),
]
BASS_DRIVE = [
    ("R", "R", "R", "R", "R", "R", "R", "R"),
    ("R", "8", "R", "8", "R", "8", "R", "8"),
    ("R", "R", "8", "R", "R", "R", "5", "R"),
    ("R", None, "R", "R", None, "R", "5", "R"),
    ("R", "R", "5", "R", "8", "R", "5", "R"),
]


def _bass_root(ctx: Ctx, s: PartSpec, chord: Chord) -> int:
    return lowest_pitch_with_pc(chord.root_pc, s.lo + 4, s.lo + 15)


def _bass_pitch(ctx: Ctx, s: PartSpec, role: str, bar: int, rng: random.Random) -> int:
    chord, nxt = ctx.chord(bar), ctx.chord(bar + 1)
    root = _bass_root(ctx, s, chord)
    idx = ctx.key.index_of(root)
    if role == "R":
        return root
    if role == "5":
        return ctx.key.pitch(idx + 4)
    if role == "8":
        return fold(root + 12, s.lo, s.hi)
    if role == "3":
        return ctx.key.pitch(idx + 2)
    if role == "APP":
        n = ctx.key.index_of(_bass_root(ctx, s, nxt))
        return ctx.key.pitch(n + rng.choice([-1, 1]))
    if role == "T":  # tonic pedal
        return lowest_pitch_with_pc(ctx.key.tonic, s.lo + 4, s.lo + 15)
    raise ValueError(role)


def w_roots(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Roots, fifths and octaves in longer values; approach notes into phrase starts."""
    part = new_part(s, "bass", mono=True)
    patterns = o.get("patterns", BASS_ROOTS)
    base_w = [3, 2, 1, 1, 1.5, 1.5][: len(patterns)] + [1] * max(0, len(patterns) - 6)
    favourite = rng.randrange(len(patterns))
    for bar in range(ctx.grid.bars):
        end = bar % PHRASE_BARS == PHRASE_BARS - 1
        w = [b * (4 if i == favourite else 1) for i, b in enumerate(base_w)]
        if end:
            w = [x * (5 if any(r == "APP" for _, r, _ in p) else 1) for x, p in zip(w, patterns)]
        for beat, role, dur in weighted_choice(rng, patterns, w):
            part.add(ctx.t(bar, beat), ctx.beats(dur * o.get("artic", 0.9)), _bass_pitch(ctx, s, role, bar, rng),
                     vel(rng, s.vel + (6 if beat == 0 else 0)))
    return [part]


def w_drive(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Driving eighths (or sixteenths with rate=0.25) with approach notes into chord changes."""
    part = new_part(s, "bass", mono=True)
    rate = o.get("rate", 0.5)
    patterns = o.get("patterns", BASS_DRIVE)
    favourite = rng.randrange(len(patterns))
    slots = int(round(ctx.bpb / rate))
    for bar in range(ctx.grid.bars):
        roles = list(weighted_choice(rng, patterns, [4 if i == favourite else 1 for i in range(len(patterns))]))
        roles = (roles * (slots // len(roles) + 1))[:slots]
        if ctx.chord(bar + 1) != ctx.chord(bar) and rng.random() < 0.6:
            roles[-1] = "APP"
        for i, role in enumerate(roles):
            if role is None:
                continue
            part.add(ctx.t(bar, i * rate), ctx.beats(rate * o.get("artic", 0.78)), _bass_pitch(ctx, s, role, bar, rng),
                     vel(rng, s.vel + (10 if (i * rate) % 1 == 0 else 0)))
    return [part]


def w_pedal(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Tonic pedal ostinato regardless of chord (desert drive, volcano dread)."""
    part = new_part(s, "bass", mono=True)
    rhythm = o.get("rhythm", (0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5))
    length = o.get("length", 0.4)
    for bar in range(ctx.grid.bars):
        for i, on in enumerate(rhythm):
            nxt = rhythm[i + 1] if i + 1 < len(rhythm) else ctx.bpb
            role = "8" if o.get("octaves") and i % 2 == 1 else "T"
            pitch = _bass_pitch(ctx, s, "T", bar, rng)
            if role == "8":
                pitch = fold(pitch + 12, s.lo, s.hi)
            part.add(ctx.t(bar, on), ctx.beats(min(length, nxt - on)), pitch, vel(rng, s.vel + (8 if on == 0 else 0)))
    return [part]


def w_walk(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Quarter-note walking line: root, chord tone or step, then a diatonic approach."""
    part = new_part(s, "bass", mono=True)
    for bar in range(ctx.grid.bars):
        root = _bass_root(ctx, s, ctx.chord(bar))
        idx = ctx.key.index_of(root)
        nxt = ctx.key.index_of(_bass_root(ctx, s, ctx.chord(bar + 1)))
        line = [idx, idx + rng.choice([1, 2, 4]), idx + rng.choice([2, 4, 5]), nxt + rng.choice([-1, 1])]
        for i, li in enumerate(line):
            pitch = fold(ctx.key.pitch(li), s.lo, s.hi)
            part.add(ctx.t(bar, i), ctx.beats(o.get("artic", 0.85)), pitch, vel(rng, s.vel + (6 if i == 0 else 0)))
    return [part]


def w_bass_sustain(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Whole-note roots (spacious levels)."""
    part = new_part(s, "bass", mono=True)
    for bar in range(ctx.grid.bars):
        part.add(ctx.t(bar), ctx.beats(ctx.bpb * 0.95), _bass_root(ctx, s, ctx.chord(bar)), vel(rng, s.vel, 3))
    return [part]


# ---------------------------------------------------------------- lead


def make_germ(seed: int, area: str, key: Key) -> Motif:
    """A one-bar motif derived from the seed alone, shared by every cue of the level."""
    rng = sub_rng(seed, area, "germ")
    rhythm = list(weighted_choice(rng, GERM_CELLS, GERM_WEIGHTS))
    tonic_chord = key.chord("i")
    centre = key.index_of(lowest_pitch_with_pc(key.tonic, 62, 73))
    start = centre + weighted_choice(rng, [0, 2, 4], [3, 2, 2])
    notes, _, _ = write_melody(rng, StepMarkov(), key, lambda _: tonic_chord, rhythm,
                               start_beat=0, start_index=start - 1, lo_index=centre - 3, hi_index=centre + 9)
    first = notes[0].index
    return Motif(tuple(n.index - first for n in notes), tuple(n.duration for n in notes))


def _fit(motif: Motif, beats: float) -> Motif:
    offsets, durations, total = [], [], 0.0
    for off, dur in zip(motif.offsets, motif.durations):
        if total >= beats - 1e-9:
            break
        dur = min(dur, beats - total)
        offsets.append(off)
        durations.append(dur)
        total += dur
    if total < beats - 1e-9:
        offsets.append(None)
        durations.append(beats - total)
    return Motif(tuple(offsets), tuple(durations), motif.source)


def _place(motif: Motif, ctx: Ctx, beat: float, target: int, lo: int, hi: int) -> list[MelodyNote]:
    sounding = [o for o in motif.offsets if o is not None]
    if not sounding:
        return []
    chord = ctx.chord_at(beat)
    tones = [i for i in range(lo, hi + 1) if chord.contains(ctx.key.pitch(i))]
    first = min(tones, key=lambda i: (abs(i - target), i))
    while first + max(sounding) > hi and first - 7 + min(sounding) >= lo:
        first -= 7
    while first + min(sounding) < lo:
        first += 7
    notes, b = [], beat
    for off, dur in zip(motif.offsets, motif.durations):
        if off is not None:
            notes.append(MelodyNote(b, dur, min(hi, max(lo, first + off))))
        b += dur
    return notes


# Phrase plans. Each phrase is a list of segments filling PHRASE_BARS bars:
#   ("motif", bars, augment, invert, shift) | ("free", bars) | ("held", bars) | ("rest", bars)
PLANS: dict[str, Callable[[int], list[tuple]]] = {
    "breath": lambda ph: [("motif", 2, 2, ph % 4 == 2, [0, 2, 0, 0][ph % 4]), ("free", 1), ("held", 1)],
    "drive": lambda ph: ([("motif", 1, 1, True, 0), ("free", 3)] if ph % 4 == 2 else
                         [("motif", 1, 1, False, 0), ("motif", 1, 1, False, [1, 2, 0, 2][ph % 4]), ("free", 2)]),
    "call": lambda ph: [("motif", 1, 1, False, 0), ("rest", 1), ("motif", 1, 1, ph % 2 == 1, 2), ("held", 1)],
    "sparse": lambda ph: ([("motif", 2, 2, False, 0), ("rest", 2)] if ph % 2 == 0 else [("rest", 1), ("free", 2), ("rest", 1)]),
    "flow": lambda ph: ([("motif", 1, 1, ph % 4 == 2, 0), ("free", 3)] if ph % 2 == 0 else [("free", 4)]),
    "answer": lambda ph: ([("motif", 2, 1, False, 0), ("free", 2)] if ph % 2 == 0 else [("free", 2), ("motif", 1, 1, True, 2), ("held", 1)]),
}


def w_melody(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Motif-based Markov melody. opts: plan, cells, artic, echo (delay in beats, 0 = none)."""
    part = new_part(s, "lead", mono=True)
    key, bpb = ctx.key, ctx.bpb
    idx = key.indices_in_range(s.lo, s.hi)
    lo, hi = idx[0], idx[-1]
    home = (lo + hi) // 2 - 1
    cells, weights = CELLS[o.get("cells", "medium")]
    plan = PLANS[o.get("plan", "breath")]
    artic = o.get("artic", 0.9)
    notes: list[MelodyNote] = []
    last, history = home, []
    for ph in range(ctx.phrases):
        beat = ph * PHRASE_BARS * bpb
        target = home
        for seg in plan(ph):
            kind, bars = seg[0], seg[1]
            beats = bars * bpb
            if kind == "motif":
                _, _, augment, invert, shift = seg
                m = ctx.germ.augment(augment) if augment != 1 else ctx.germ
                m = _fit(m.invert() if invert else m, beats)
                stated = _place(m, ctx, beat, target + shift, lo, hi)
                if stated:
                    notes += stated
                    target = stated[0].index
                    last = stated[-1].index
                    history = [b.index - a.index for a, b in zip(stated, stated[1:])][-2:]
            elif kind == "free":
                rhythm = choose_cells(rng, cells, weights, beats)
                free, last, history = write_melody(rng, ctx.markov, key, ctx.chord_at, rhythm, beat, last, lo, hi, history)
                notes += free
            elif kind == "held":
                held, last, history = write_melody(rng, ctx.markov, key, ctx.chord_at, [(beats / 2, F), (beats / 2, R)],
                                                   beat, last, lo, hi, history)
                notes += held
            beat += beats
    for n in notes:
        strong = abs(n.beat % 2) < 1e-9
        part.add(ctx.grid.beat_ticks(n.beat), round(n.duration * ctx.grid.ppq * artic), key.pitch(n.index),
                 vel(rng, s.vel + (8 if strong else 0)))
    parts = [part]
    if o.get("echo"):
        echo = Part(part.name + "_echo", program=s.program, lo=s.lo, hi=s.hi, pan=128 - s.pan, volume=s.volume)
        delay = ctx.beats(o["echo"])
        total = ctx.grid.total_ticks
        for n in part.notes:
            start = (n.start + delay) % total
            echo.add(start, min(n.duration, total - start), n.pitch, int(n.velocity * 0.5))
        parts.append(echo)
    return parts


# ---------------------------------------------------------------- danger / colour writers


def w_drone(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Tonic and fifth held for each phrase. opts: swell (beats)."""
    part = new_part(s, "drone")
    tonic = lowest_pitch_with_pc(ctx.key.tonic, s.lo, s.lo + 11)
    fifth = ctx.key.pitch(ctx.key.index_of(tonic) + 4)
    for ph in range(ctx.phrases):
        for p in (tonic, fifth):
            part.add(ctx.t(ph * PHRASE_BARS), ctx.beats(PHRASE_BARS * ctx.bpb), p, vel(rng, s.vel, 3))
    if o.get("swell"):
        swell_controls(part, ctx, o["swell"], low=o.get("swell_low", 50))
    return [part]


HIT_BARS = {
    "every": lambda bar: True,
    "odd": lambda bar: bar % 2 == 0,
    "phrase": lambda bar: bar % PHRASE_BARS == 0,
}


def w_hits(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Low hits on chord roots (timpani, taiko, brass, orchestra hit).

    opts: bars ("every" | "odd" | "phrase"), beats (onsets in the bar), roll (16th roll before each phrase).
    """
    part = new_part(s, "hits")
    when = HIT_BARS[o.get("bars", "odd")]
    beats = o.get("beats", (0,))
    for bar in range(ctx.grid.bars):
        root = fold(lowest_pitch_with_pc(ctx.chord(bar).root_pc, s.lo, s.lo + 11), s.lo, s.hi)
        roll_bar = o.get("roll") and bar % PHRASE_BARS == PHRASE_BARS - 1
        if when(bar):
            for i, b in enumerate(beats):
                if roll_bar and b >= 3:
                    continue
                part.add(ctx.t(bar, b), ctx.beats(o.get("length", 1.0)), root, vel(rng, s.vel + (6 if i == 0 else 0), 4))
        if roll_bar:
            nxt = fold(lowest_pitch_with_pc(ctx.chord(bar + 1).root_pc, s.lo, s.lo + 11), s.lo, s.hi)
            for i in range(4):
                part.add(ctx.t(bar, 3 + i * 0.25), ctx.beats(0.25), nxt, s.vel - 25 + 12 * i)
    return [part]


def w_tremolo(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Chord root and fifth (or third) held per bar, high up."""
    part = new_part(s, "tremolo")
    interval = o.get("interval", 4)
    for bar in range(ctx.grid.bars):
        root = fold(lowest_pitch_with_pc(ctx.chord(bar).root_pc, s.lo, s.lo + 11), s.lo, s.hi - 7)
        for p in (root, ctx.key.pitch(ctx.key.index_of(root) + interval)):
            part.add(ctx.t(bar), ctx.beats(ctx.bpb), p, vel(rng, s.vel, 3))
    return [part]


OSTINATO_SHAPES = [(0, 1, 0, 2, 0, 1, 0, -1), (0, 0, 1, 0, 2, 0, 1, 0), (0, 2, 1, 0, 0, 2, 1, -1), (0, 4, 2, 4, 0, 4, 2, 1), (0, 1, 2, 1, 0, -1, 0, 1)]


def w_ostinato(ctx: Ctx, s: PartSpec, rng: random.Random, o: dict) -> list[Part]:
    """Repeating scale figure on each chord root. opts: rate, shape index (seeded otherwise)."""
    part = new_part(s, "ostinato", mono=True)
    rate = o.get("rate", 0.5)
    shape = OSTINATO_SHAPES[o["shape"]] if "shape" in o else rng.choice(OSTINATO_SHAPES)
    for bar in range(ctx.grid.bars):
        base = ctx.key.index_of(lowest_pitch_with_pc(ctx.chord(bar).root_pc, s.lo + 3, s.lo + 14))
        for i in range(int(round(ctx.bpb / rate))):
            pitch = fold(ctx.key.pitch(base + shape[i % len(shape)]), s.lo, s.hi)
            part.add(ctx.t(bar, i * rate), ctx.beats(rate * o.get("artic", 0.8)), pitch,
                     vel(rng, s.vel + (10 if (i * rate) % 1 == 0 else 0)))
    return [part]


WRITERS: dict[str, Callable[[Ctx, PartSpec, random.Random, dict], list[Part]]] = {
    "sustain": w_sustain, "stabs": w_stabs, "arp": w_arp, "pulse": w_pulse, "strum": w_strum,
    "sparkle": w_sparkle, "texture": w_texture,
    "roots": w_roots, "drive": w_drive, "pedal": w_pedal, "walk": w_walk, "bass_sustain": w_bass_sustain,
    "melody": w_melody,
    "drone": w_drone, "hits": w_hits, "tremolo": w_tremolo, "ostinato": w_ostinato,
}

# ---------------------------------------------------------------- drums


def write_drums(ctx: Ctx, d: DrumSpec, rng: random.Random) -> Part:
    part = Part("kit", program=d.kit, lo=27, hi=87, drums=True, volume=d.volume)
    chosen = [rng.randrange(len(v.patterns)) for v in d.voices]
    for bar in range(ctx.grid.bars):
        fill_bar = bool(d.fills) and bar % PHRASE_BARS == PHRASE_BARS - 1
        fill = rng.choice(d.fills) if fill_bar else ()
        fill_start = min(b for b, _ in fill) if fill else ctx.bpb
        hits: dict[tuple[int, int], int] = {}
        for v, main in zip(d.voices, chosen):
            pattern = v.patterns[main]
            if len(v.patterns) > 1 and rng.random() < v.alt:
                pattern = v.patterns[rng.randrange(len(v.patterns))]
            for on in pattern:
                if on >= fill_start and v.note not in (35, 36):
                    continue
                if rng.random() >= v.prob:
                    continue
                accent = v.accent if on == 0 else (v.accent // 2 if on % 1 == 0 else 0)
                hits[(ctx.t(bar, on), v.note)] = vel(rng, v.vel + accent, 4)
        for i, (b, note) in enumerate(fill):
            hits[(ctx.t(bar, b), note)] = 72 + 40 * i // max(1, len(fill) - 1)
        if d.crash and bar % PHRASE_BARS == 0:
            hits[(ctx.t(bar), d.crash)] = vel(rng, 98, 3)
        for (tick, note), v_ in sorted(hits.items()):
            part.add(tick, ctx.grid.ppq // 4, note, v_)
    return part


# ---------------------------------------------------------------- entry point


def _alternatives(options: list) -> list[tuple[PartSpec, ...]]:
    return [o if isinstance(o, tuple) else (o,) for o in options]


def arrange(level: LevelSpec, seed: int, bpm: int | None = None, key: str | None = None, bars: int | None = None,
            cue: str | None = None, motif: Motif | None = None) -> Arrangement:
    cue = cue or next(iter(level.cues))
    if cue not in level.cues:
        raise ValueError(f"unknown cue {cue!r} for {level.area}; expected one of {list(level.cues)}")
    spec = level.cues[cue]
    bars = bars or level.bars
    if bars % PHRASE_BARS:
        raise ValueError(f"bars must be a multiple of {PHRASE_BARS}")
    grid = Grid(bpm or spec.bpm, bars)
    k = Key.parse(key or level.key)

    # Seed-level choices shared by every cue of this seed.
    level_rng = sub_rng(seed, level.area, "progression")
    progression = level_rng.choice(level.progressions)
    if bars % len(progression):
        raise ValueError(f"progression length {len(progression)} does not divide {bars} bars")
    romans = [progression[b % len(progression)] for b in range(bars)]
    germ = motif or make_germ(seed, level.area, k)
    markov = StepMarkov(training=[germ.steps] if germ.steps else ())
    ctx = Ctx(level.area, cue, seed, k, grid, romans, germ, markov)

    stems: dict[str, list[Part]] = {}
    for stem in STEMS:
        rng = sub_rng(seed, level.area, cue, stem)
        if stem == "percussion":
            stems[stem] = [write_drums(ctx, rng.choice(spec.percussion), rng)]
            continue
        parts: list[Part] = []
        for ps in rng.choice(_alternatives(getattr(spec, stem))):
            parts += WRITERS[ps.writer](ctx, ps, rng, resolve(ps.opts, rng))
        names: dict[str, int] = {}
        for p in parts:  # track names must be unique within a stem
            n = names[p.name] = names.get(p.name, 0) + 1
            if n > 1:
                p.name = f"{p.name}_{n}"
        stems[stem] = parts
    return Arrangement(level.area, cue, seed, k, grid, romans, stems)


def module_exports(level: LevelSpec) -> dict:
    """Attributes every generator module exposes to render/make_stems.py."""
    return {
        "AREA": level.area,
        "KEY": level.key,
        "BARS": level.bars,
        "CUES": {name: {"bpm": c.bpm} for name, c in level.cues.items()},
        "STEMS": STEMS,
        "FX": level.fx,
    }
