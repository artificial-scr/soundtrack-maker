"""Bar grid: converts bars and beats to MIDI ticks, seconds and samples."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

PPQ = 480
SAMPLE_RATE = 48_000


@dataclass(frozen=True)
class Grid:
    bpm: int
    bars: int
    beats_per_bar: int = 4
    ppq: int = PPQ
    sample_rate: int = SAMPLE_RATE

    def __post_init__(self) -> None:
        if self.bpm <= 0 or self.bars <= 0:
            raise ValueError("bpm and bars must be positive")
        if self._samples_per_bar_exact().denominator != 1:
            raise ValueError(
                f"{self.bpm} BPM does not give a whole number of samples per bar at "
                f"{self.sample_rate} Hz; pick another tempo so loops can be cut exactly"
            )

    def _samples_per_bar_exact(self) -> Fraction:
        return Fraction(self.sample_rate * 60 * self.beats_per_bar, self.bpm)

    @property
    def total_beats(self) -> int:
        return self.bars * self.beats_per_bar

    @property
    def ticks_per_bar(self) -> int:
        return self.ppq * self.beats_per_bar

    @property
    def total_ticks(self) -> int:
        return self.bars * self.ticks_per_bar

    @property
    def tempo_us(self) -> int:
        """Microseconds per quarter note, as stored in a MIDI set_tempo event."""
        us = Fraction(60_000_000, self.bpm)
        if us.denominator != 1:
            raise ValueError(f"{self.bpm} BPM is not representable exactly as a MIDI tempo")
        return int(us)

    @property
    def samples_per_bar(self) -> int:
        return int(self._samples_per_bar_exact())

    @property
    def total_samples(self) -> int:
        return self.bars * self.samples_per_bar

    @property
    def seconds_per_bar(self) -> float:
        return 60.0 * self.beats_per_bar / self.bpm

    @property
    def total_seconds(self) -> float:
        return self.bars * self.seconds_per_bar

    def beat_ticks(self, beat: float) -> int:
        """Absolute beat position (from the start of the loop) to ticks."""
        ticks = Fraction(beat).limit_denominator(64) * self.ppq
        if ticks.denominator != 1:
            raise ValueError(f"beat {beat} does not fall on the tick grid")
        return int(ticks)

    def bar_beat(self, bar: int, beat: float = 0.0) -> float:
        return bar * self.beats_per_bar + beat
