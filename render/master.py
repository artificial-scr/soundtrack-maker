"""Per-stem effects and loudness mastering.

Loudness is set on the full mix (all stems summed) to -16 LUFS. The same gain and the same
limiter gain envelope are applied to every stem, so the stems still sum to the mastered mix
and their relative balance is kept.
"""

from __future__ import annotations

import numpy as np
import pyloudnorm
from pedalboard import Compressor, Delay, Gain, HighpassFilter, LowpassFilter, Pedalboard, Reverb
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import resample_poly

TARGET_LUFS = -16.0
CEILING_DBTP = -1.0
LIMITER_CEILING_DB = -1.3  # a little under the ceiling to cover the inter-sample estimate
LIMITER_WINDOW_MS = 10.0

# Per-stem chain. Balance between stems is set here and by MIDI velocities. A level can
# override any key per stem through its spec's `fx` (e.g. {"lead": {"lowpass": 3000}}).
# Keys: highpass, lowpass (Hz); compressor (threshold dB, ratio); chorus (rate Hz, depth, mix);
# delay (beats, feedback, mix); reverb (room size, wet); gain_db.
STEM_FX = {
    "pads": {"highpass": 110, "reverb": (0.6, 0.22), "gain_db": -2.0},
    "bass": {"highpass": 32, "compressor": (-20, 2.5), "gain_db": 0.0},
    "percussion": {"highpass": 30, "compressor": (-16, 2.0), "reverb": (0.25, 0.07), "gain_db": -1.0},
    "lead": {"highpass": 160, "reverb": (0.5, 0.18), "gain_db": -1.5},
    "danger": {"highpass": 40, "reverb": (0.6, 0.2), "gain_db": -3.0},
}


def _fx(stem: str, overrides: dict | None) -> dict:
    return {**STEM_FX[stem], **(overrides or {})}


def pre_board(fx: dict) -> Pedalboard:
    """Filters and dynamics, applied before the chorus."""
    board = [HighpassFilter(cutoff_frequency_hz=fx["highpass"])]
    if fx.get("lowpass"):
        board.append(LowpassFilter(cutoff_frequency_hz=fx["lowpass"]))
    if "compressor" in fx:
        threshold, ratio = fx["compressor"]
        board.append(Compressor(threshold_db=threshold, ratio=ratio, attack_ms=8, release_ms=120))
    return Pedalboard(board)


def loop_chorus(audio: np.ndarray, sample_rate: int, loop_frames: int, rate_hz: float, depth: float, mix: float,
                centre_ms: float = 7.0) -> np.ndarray:
    """Chorus whose modulation is a pure function of the position in the loop.

    pedalboard's Chorus accumulates its LFO phase in floating point, which drifts over a loop
    and leaves a jump at the loop point. Here the delay is computed from (sample index mod
    loop length) with a whole number of LFO cycles per loop, so it is exactly periodic.
    Channels are modulated a quarter cycle apart for width. depth 0..1 maps to 0..8 ms.
    """
    cycles = max(1, round(rate_hz * loop_frames / sample_rate))
    n = np.arange(len(audio))
    phase = 2 * np.pi * cycles * (n % loop_frames) / loop_frames
    out = np.empty_like(audio)
    for c in range(audio.shape[1]):
        delay = (centre_ms + depth * 8.0 * 0.5 * (1 + np.sin(phase + c * np.pi / 2))) * sample_rate / 1000
        pos = n - delay
        i0 = np.floor(pos).astype(np.int64)
        frac = pos - i0
        i0c, i1c = np.clip(i0, 0, len(audio) - 1), np.clip(i0 + 1, 0, len(audio) - 1)
        wet = audio[i0c, c] * (1 - frac) + audio[i1c, c] * frac
        wet[i0 < 0] = 0.0
        out[:, c] = (1 - mix) * audio[:, c] + mix * wet
    return out


def stem_board(stem: str, overrides: dict | None = None, bpm: float = 120.0) -> Pedalboard:
    """Time-based effects and gain, applied after the chorus."""
    fx = _fx(stem, overrides)
    board = []
    if fx.get("delay"):
        beats, feedback, mix = fx["delay"]
        board.append(Delay(delay_seconds=beats * 60.0 / bpm, feedback=feedback, mix=mix))
    if fx.get("reverb"):
        room, wet = fx["reverb"]
        board.append(Reverb(room_size=room, wet_level=wet, dry_level=1.0, damping=0.5, width=1.0))
    board.append(Gain(gain_db=fx["gain_db"]))
    return Pedalboard(board)


def apply_fx(stem: str, audio: np.ndarray, sample_rate: int, overrides: dict | None = None, bpm: float = 120.0,
             loop_frames: int | None = None) -> np.ndarray:
    """audio is (frames, channels), laid out as whole loops; pedalboard wants (channels, frames)."""
    fx = _fx(stem, overrides)
    out = pre_board(fx)(audio.T.astype(np.float32), sample_rate, reset=True).T.astype(np.float64)
    if fx.get("chorus"):
        rate, depth, mix = fx["chorus"]
        out = loop_chorus(out, sample_rate, loop_frames or len(out), rate, depth, mix)
    out = stem_board(stem, overrides, bpm)(out.T.astype(np.float32), sample_rate, reset=True)
    return out.T.astype(np.float64)


def true_peak_db(audio: np.ndarray) -> float:
    """4x oversampled peak (ITU-R BS.1770 style estimate), in dBTP."""
    up = resample_poly(audio.astype(np.float32), 4, 1, axis=0)
    peak = max(float(np.max(np.abs(up))), 1e-12)
    return 20 * np.log10(peak)


def integrated_lufs(audio: np.ndarray, sample_rate: int) -> float:
    return float(pyloudnorm.Meter(sample_rate).integrated_loudness(audio))


def limiter_envelope(audio: np.ndarray, sample_rate: int, ceiling_db: float = LIMITER_CEILING_DB) -> np.ndarray:
    """Gain envelope (frames,) that keeps the oversampled peak under the ceiling.

    Computed circularly (one second of the loop's tail is prepended and of its head appended)
    so the envelope is continuous across the loop point. Min filter then box smoothing
    guarantees the smoothed gain never exceeds the gain each sample needs.
    """
    n = len(audio)
    pad = min(n, sample_rate)
    wrapped = np.vstack([audio[-pad:], audio, audio[:pad]]).astype(np.float32)
    up = np.abs(resample_poly(wrapped, 4, 1, axis=0)).max(axis=1)
    peak = up[: 4 * len(wrapped)].reshape(-1, 4).max(axis=1)
    del up
    ceiling = 10 ** (ceiling_db / 20)
    need = np.minimum(1.0, ceiling / np.maximum(peak, 1e-12))
    w = max(1, int(sample_rate * LIMITER_WINDOW_MS / 1000))
    env = uniform_filter1d(minimum_filter1d(need, size=2 * w + 1, mode="nearest"), size=w, mode="nearest")
    return np.minimum(env, need)[pad : pad + n].astype(np.float64)


def master(stems: dict[str, np.ndarray], sample_rate: int) -> tuple[dict[str, np.ndarray], dict]:
    """Return mastered stems and a report. Iterates gain and limiting to land on target."""
    mix = sum(stems.values())
    gain = 1.0
    env = np.ones(len(mix))
    for _ in range(4):
        lufs = integrated_lufs(mix * gain * env[:, None], sample_rate)
        gain *= 10 ** ((TARGET_LUFS - lufs) / 20)
        env = limiter_envelope(mix * gain, sample_rate)
    scale = (gain * env)[:, None]
    out = {name: audio * scale for name, audio in stems.items()}
    mastered_mix = mix * scale
    report = {
        "target_lufs": TARGET_LUFS,
        "mix_lufs": round(integrated_lufs(mastered_mix, sample_rate), 2),
        "mix_true_peak_dbtp": round(true_peak_db(mastered_mix), 2),
        "gain_db": round(20 * np.log10(gain), 2),
        "max_limiter_reduction_db": round(max(0.0, -20 * np.log10(env.min())), 2),
        "limited_fraction": round(float(np.mean(env < 0.999)), 4),
    }
    return out, report
