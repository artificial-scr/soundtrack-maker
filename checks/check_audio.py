"""Audio checks: lengths, loop seam, silence and clipping, loudness and true peak."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from render.master import CEILING_DBTP, TARGET_LUFS, integrated_lufs, true_peak_db

from .common import Result, load_build, stem_files

LUFS_TOLERANCE = 1.0
SILENCE_DBFS = -60.0
SEAM_CONTEXT = 4800  # 100 ms either side of the loop point
SEAM_MAX_RATIO = 1.5


def _rms_db(x: np.ndarray) -> float:
    return 20 * np.log10(max(np.sqrt(np.mean(x**2)), 1e-12))


def seam_ratio(audio: np.ndarray) -> float:
    """Sample-to-sample jump across the loop point, relative to the jumps around it.

    A seamless loop scores at most about 1 (the seam is no steeper than the signal around it);
    a click scores far above it.
    """
    wrapped = np.vstack([audio[-SEAM_CONTEXT:], audio[:SEAM_CONTEXT]])
    diffs = np.abs(np.diff(wrapped, axis=0)).max(axis=1)
    seam = diffs[SEAM_CONTEXT - 1]
    typical = np.percentile(diffs, 99.5)
    return float(seam / max(typical, 1e-9))


def check_seed(seed_dir: Path) -> list[Result]:
    meta = load_build(seed_dir)
    label = f"{meta['area']}/{meta['cue']}/seed{meta['seed']}"
    sr, expected = meta["sample_rate"], meta["total_samples"]
    results: list[Result] = []
    stems: dict[str, np.ndarray] = {}

    for ext in ("wav", "ogg"):
        for stem, path in stem_files(seed_dir, meta, ext).items():
            target = f"{label} {stem}.{ext}"
            if not path.exists():
                results.append(Result("audio exists", target, False, str(path)))
                continue
            info = sf.info(path)
            results.append(Result("duration = bar grid", target, info.frames == expected and info.samplerate == sr,
                                  f"{info.frames} frames @ {info.samplerate} Hz, expected {expected} @ {sr}"))
            if ext == "wav":
                stems[stem] = sf.read(path, dtype="float64", always_2d=True)[0]

    for stem, audio in stems.items():
        target = f"{label} {stem}"
        rms = _rms_db(audio)
        results.append(Result("not silent", target, rms > SILENCE_DBFS, f"RMS {rms:.1f} dBFS"))
        clipped = int(np.sum(np.abs(audio) >= 0.999))
        results.append(Result("not clipped", target, clipped == 0, f"{clipped} samples at full scale"))
        tp = true_peak_db(audio)
        results.append(Result("stem true peak", target, tp <= CEILING_DBTP, f"{tp:.2f} dBTP (ceiling {CEILING_DBTP})"))
        ratio = seam_ratio(audio)
        results.append(Result("loop seam", target, ratio < SEAM_MAX_RATIO, f"seam jump {ratio:.2f}x the 99.5th pct of nearby jumps"))

    if stems and len({len(a) for a in stems.values()}) == 1:
        mix = sum(stems.values())
        lufs = integrated_lufs(mix, sr)
        tp = true_peak_db(mix)
        results.append(Result("mix loudness", f"{label} mix", abs(lufs - TARGET_LUFS) <= LUFS_TOLERANCE,
                              f"{lufs:.2f} LUFS (target {TARGET_LUFS} +/- {LUFS_TOLERANCE})"))
        results.append(Result("mix true peak", f"{label} mix", tp <= CEILING_DBTP, f"{tp:.2f} dBTP"))
        ratio = seam_ratio(mix)
        results.append(Result("loop seam", f"{label} mix", ratio < SEAM_MAX_RATIO, f"seam jump {ratio:.2f}x"))
    return results
