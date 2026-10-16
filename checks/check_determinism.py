"""Rebuild a seed in a temp dir and compare against the existing build.

MIDI and WAV must be byte-identical. Ogg files embed a random stream serial number, so the
decoded Ogg audio is compared instead of the file bytes.
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from render.make_stems import build_one

from .common import Result, load_build, stem_files


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_seed(seed_dir: Path, soundfont: Path) -> list[Result]:
    meta = load_build(seed_dir)
    label = f"{meta['area']}/{meta['cue']}/seed{meta['seed']}"
    results: list[Result] = []
    with tempfile.TemporaryDirectory() as tmp:
        build_one(meta["area"], meta["cue"], meta["seed"], Path(tmp), soundfont,
                  bpm=meta["bpm"], key=meta["key"], bars=meta["bars"], previews=False)
        fresh = Path(tmp) / meta["area"] / meta["cue"] / f"seed{meta['seed']}"
        for ext in ("mid", "wav"):
            old, new = stem_files(seed_dir, meta, ext), stem_files(fresh, meta, ext)
            diff = [s for s in old if _sha(old[s]) != _sha(new[s])]
            results.append(Result(f"deterministic .{ext}", label, not diff,
                                  f"differs: {diff}" if diff else "byte-identical rebuild"))
        old, new = stem_files(seed_dir, meta, "ogg"), stem_files(fresh, meta, "ogg")
        diff = [s for s in old if not np.array_equal(sf.read(old[s])[0], sf.read(new[s])[0])]
        results.append(Result("deterministic .ogg", label, not diff,
                              f"differs: {diff}" if diff else "identical decoded audio"))
    return results
