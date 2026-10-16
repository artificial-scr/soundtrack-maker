"""Copy the seeds you chose into a clean folder with stable file names.

    python -m render.export volcano:3 meadow:5            # same seed for every cue of a level
    python -m render.export volcano.calm:3 volcano.action:7  # pick per cue
    python -m render.export keep:2 --wav --out ~/mygame/assets/music

Result (per level):
    export/volcano/volcano_calm_pads.ogg ... volcano_calm_danger.ogg     (stems)
    export/volcano/volcano_calm_mix.ogg                                  (full mix)
    export/volcano/selection.json                                        (which seed, key, BPM, bars...)
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from pathlib import Path

from generators import AREAS
from render.make_stems import ROOT, STEMS_DIR

DEFAULT_OUT = ROOT / "export"


def parse_pick(text: str) -> tuple[str, str | None, int]:
    """'volcano:3' -> ('volcano', None, 3); 'volcano.action:7' -> ('volcano', 'action', 7)."""
    target, _, seed = text.partition(":")
    if not seed.isdigit():
        raise argparse.ArgumentTypeError(f"expected LEVEL:SEED or LEVEL.CUE:SEED, got {text!r}")
    area, _, cue = target.partition(".")
    return area, cue or None, int(seed)


def export_cue(area: str, cue: str, seed: int, stems_root: Path, out: Path, wav: bool) -> dict:
    src = stems_root / area / cue / f"seed{seed}"
    meta_path = src / "build.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"{area}/{cue} seed {seed} has not been built (missing {src}). "
                                f"Run: make level LEVEL={area} SEEDS={seed}")
    meta = json.loads(meta_path.read_text())
    dest = out / area
    dest.mkdir(parents=True, exist_ok=True)
    exts = ["ogg", "wav"] if wav else ["ogg"]
    for stem in meta["stems"]:
        for ext in exts:
            shutil.copy2(src / f"{area}_{cue}_{stem}_seed{seed}.{ext}", dest / f"{area}_{cue}_{stem}.{ext}")
    preview = stems_root / area / "previews" / f"{area}_{cue}_mix_seed{seed}.ogg"
    if preview.exists():
        shutil.copy2(preview, dest / f"{area}_{cue}_mix.ogg")
    return {
        "seed": seed,
        "bpm": meta["bpm"],
        "bars": meta["bars"],
        "beats_per_bar": meta["beats_per_bar"],
        "key": meta["key"],
        "loop_seconds": meta["total_samples"] / meta["sample_rate"],
        "loop_samples": meta["total_samples"],
        "sample_rate": meta["sample_rate"],
        "stems": list(meta["stems"]),
        "mix_lufs": meta["master"]["mix_lufs"],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("picks", nargs="+", type=parse_pick, metavar="LEVEL[.CUE]:SEED")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--stems", type=Path, default=STEMS_DIR)
    ap.add_argument("--wav", action="store_true", help="also copy the 24-bit WAV masters")
    args = ap.parse_args(argv)

    selections: dict[str, dict] = {}
    for area, cue, seed in args.picks:
        if area not in AREAS:
            ap.error(f"unknown level {area!r}; choose from: {', '.join(AREAS)}")
        gen = importlib.import_module(f"generators.{area}")
        cues = [cue] if cue else list(gen.CUES)
        for c in cues:
            if c not in gen.CUES:
                ap.error(f"{area} has no cue {c!r}; cues: {', '.join(gen.CUES)}")
            try:
                selections.setdefault(area, {})[c] = export_cue(area, c, seed, args.stems, args.out, args.wav)
            except FileNotFoundError as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
            print(f"{area}/{c}: seed {seed} -> {args.out / area}")

    for area, cues in selections.items():
        path = args.out / area / "selection.json"
        existing = json.loads(path.read_text()) if path.exists() else {}
        existing.update(cues)
        path.write_text(json.dumps(existing, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
