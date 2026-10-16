"""Render MIDI stems to audio with FluidSynth."""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOUNDFONT = ROOT / "soundfonts" / "GeneralUser-GS.sf2"
FLUIDSYNTH_GAIN = 0.6


def fluidsynth_version() -> str:
    out = subprocess.run(["fluidsynth", "--version"], capture_output=True, text=True, check=True).stdout
    return out.splitlines()[0].strip()


def render(mid: Path, wav: Path, soundfont: Path = DEFAULT_SOUNDFONT, sample_rate: int = 48_000) -> None:
    """Render to 32-bit float WAV. Built-in reverb and chorus are off (effects come later,
    under our control), and a single synth thread keeps the output bit-identical."""
    if not soundfont.exists():
        raise FileNotFoundError(f"soundfont not found: {soundfont}")
    wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "fluidsynth", "-ni", "-q",
        "-R", "0", "-C", "0",
        "-r", str(sample_rate),
        "-g", str(FLUIDSYNTH_GAIN),
        "-o", "synth.cpu-cores=1",
        "-T", "wav", "-O", "float",
        "-F", str(wav),
        str(soundfont), str(mid),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def read_exact(wav: Path, frames: int) -> np.ndarray:
    """Read a render as float64 stereo, zero-padded or truncated to exactly `frames`."""
    audio, _ = sf.read(wav, dtype="float64", always_2d=True)
    if audio.shape[1] == 1:
        audio = np.repeat(audio, 2, axis=1)
    if len(audio) < frames:
        audio = np.vstack([audio, np.zeros((frames - len(audio), audio.shape[1]))])
    return audio[:frames]
