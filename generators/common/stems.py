"""Note containers and MIDI export. One MIDI file per stem, all on the same bar grid."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import mido

from .grid import Grid
from .theory import Key

DRUM_CHANNEL = 9


@dataclass(frozen=True)
class Note:
    start: int  # ticks from loop start
    duration: int  # ticks
    pitch: int
    velocity: int

    @property
    def end(self) -> int:
        return self.start + self.duration


@dataclass
class Part:
    """One instrument inside a stem. A stem can hold several parts (e.g. strings + timpani)."""

    name: str
    program: int  # General MIDI program, 0-based
    lo: int  # playable range, MIDI numbers
    hi: int
    monophonic: bool = False
    drums: bool = False
    pan: int = 64
    volume: int = 100
    notes: list[Note] = field(default_factory=list)
    controls: list[tuple[int, int, int]] = field(default_factory=list)  # (tick, controller, value)

    def cc(self, tick: int, controller: int, value: int) -> None:
        self.controls.append((int(tick), controller, max(0, min(127, int(value)))))

    def add(self, start: int, duration: int, pitch: int, velocity: int) -> None:
        velocity = max(1, min(127, int(velocity)))
        self.notes.append(Note(int(start), max(1, int(duration)), int(pitch), velocity))

    def spec(self) -> dict:
        d = asdict(self)
        d.pop("notes")
        d.pop("controls")
        return d


@dataclass
class Arrangement:
    area: str
    cue: str
    seed: int
    key: Key
    grid: Grid
    chords: list[str]  # one roman numeral per bar
    stems: dict[str, list[Part]]

    def metadata(self) -> dict:
        return {
            "area": self.area,
            "cue": self.cue,
            "seed": self.seed,
            "key": str(self.key),
            "key_pitch_classes": list(self.key.pitch_classes),
            "bpm": self.grid.bpm,
            "bars": self.grid.bars,
            "beats_per_bar": self.grid.beats_per_bar,
            "ppq": self.grid.ppq,
            "sample_rate": self.grid.sample_rate,
            "total_ticks": self.grid.total_ticks,
            "total_samples": self.grid.total_samples,
            "chords": self.chords,
            "stems": {name: [p.spec() for p in parts] for name, parts in self.stems.items()},
        }


def stem_midi(parts: list[Part], grid: Grid, repeats: int = 1) -> mido.MidiFile:
    """Build a type-1 MIDI file whose end_of_track sits exactly on the final bar line.

    pretty_midi and most tools otherwise end a file at its last note-off, which would give
    stems different lengths. A conductor track carries tempo and time signature.
    `repeats` > 1 lays the loop out several times back to back (used for circular rendering).
    """
    end_tick = grid.total_ticks * repeats
    mid = mido.MidiFile(type=1, ticks_per_beat=grid.ppq)

    conductor = mido.MidiTrack()
    conductor.append(mido.MetaMessage("set_tempo", tempo=grid.tempo_us, time=0))
    conductor.append(
        mido.MetaMessage("time_signature", numerator=grid.beats_per_bar, denominator=4, time=0)
    )
    conductor.append(mido.MetaMessage("end_of_track", time=end_tick))
    mid.tracks.append(conductor)

    melodic_channels = iter(c for c in range(16) if c != DRUM_CHANNEL)
    for part in parts:
        channel = DRUM_CHANNEL if part.drums else next(melodic_channels)
        track = mido.MidiTrack()
        track.append(mido.MetaMessage("track_name", name=part.name, time=0))
        if not part.drums or part.program:  # on the drum channel a program change selects the kit
            track.append(mido.Message("program_change", program=part.program, channel=channel, time=0))
        track.append(mido.Message("control_change", control=7, value=part.volume, channel=channel, time=0))
        track.append(mido.Message("control_change", control=10, value=part.pan, channel=channel, time=0))
        track.append(mido.Message("control_change", control=91, value=0, channel=channel, time=0))
        track.append(mido.Message("control_change", control=93, value=0, channel=channel, time=0))

        # (tick, order, message): note-offs sort before note-ons at the same tick so a
        # repeated pitch is released before it is struck again.
        events = []
        for n in part.notes:
            if n.end > grid.total_ticks:
                raise ValueError(f"{part.name}: note at {n.start} runs past the loop end")
            for r in range(repeats):
                offset = r * grid.total_ticks
                events.append((offset + n.start, 1, n.pitch, mido.Message("note_on", note=n.pitch, velocity=n.velocity, channel=channel)))
                events.append((offset + n.end, 0, n.pitch, mido.Message("note_off", note=n.pitch, velocity=0, channel=channel)))
        for tick, controller, value in part.controls:
            for r in range(repeats):
                msg = mido.Message("control_change", control=controller, value=value, channel=channel)
                events.append((r * grid.total_ticks + tick, -1, controller, msg))
        events.sort(key=lambda e: (e[0], e[1], e[2]))

        now = 0
        for tick, _, _, msg in events:
            track.append(msg.copy(time=tick - now))
            now = tick
        track.append(mido.MetaMessage("end_of_track", time=end_tick - now))
        mid.tracks.append(track)
    return mid


def write_stem(path: Path, parts: list[Part], grid: Grid, repeats: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stem_midi(parts, grid, repeats).save(path)
