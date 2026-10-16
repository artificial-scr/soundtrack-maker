"""Run all validation checks on built stems.

    python -m checks.run                           # every level, cue and seed found
    python -m checks.run --area volcano --seeds 1-4 --determinism

Exits non-zero on any failure and writes stems/{area}/report.json.

These checks cover technical correctness only. They say nothing about whether a cue sounds
good: listen to every cue and choose which seeds to keep.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from generators import AREAS, LEVELS
from render.make_stems import STEMS_DIR, parse_seeds
from render.render_midi import DEFAULT_SOUNDFONT

from . import check_audio, check_determinism, check_midi
from .common import Result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--area", default="all", help="area name, comma-separated list, or 'all' (every level)")
    ap.add_argument("--cues", default=None)
    ap.add_argument("--seeds", default=None, help="default: every seed found")
    ap.add_argument("--stems", type=Path, default=STEMS_DIR)
    ap.add_argument("--determinism", action="store_true", help="rebuild the first seed of each cue and compare")
    ap.add_argument("--soundfont", type=Path, default=DEFAULT_SOUNDFONT)
    ap.add_argument("--verbose", "-v", action="store_true", help="print passing checks too")
    args = ap.parse_args(argv)

    areas = LEVELS if args.area == "all" else args.area.split(",")
    unknown = [a for a in areas if a not in AREAS]
    if unknown:
        ap.error(f"unknown level(s) {', '.join(unknown)}; choose from: {', '.join(AREAS)} (or 'all')")
    wanted = set(parse_seeds(args.seeds)) if args.seeds else None
    results: list[Result] = []
    for area in areas:
        results += check_area(args, area, wanted)

    for r in results:
        if args.verbose or not r.ok:
            print(r.line())
    failed = [r for r in results if not r.ok]
    by_check: dict[str, list[int]] = {}
    for r in results:
        by_check.setdefault(r.check, [0, 0])[0 if r.ok else 1] += 1
    print("\nSummary:")
    for check, (ok, bad) in by_check.items():
        print(f"  {check:<22} {ok:>5} pass  {bad:>3} fail")
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed.")
    print("These checks cover technical correctness only. Listen to every cue and choose which seeds to keep.")

    report = args.stems / ("report.json" if len(areas) > 1 else f"{areas[0]}/report.json")
    report.write_text(json.dumps([asdict(r) for r in results], indent=2) + "\n")
    return 1 if failed else 0


def check_area(args: argparse.Namespace, area: str, wanted: set[int] | None) -> list[Result]:
    area_dir = args.stems / area
    if not area_dir.is_dir():
        return [Result("area built", area, False, f"no stems in {area_dir}")]
    cues = args.cues.split(",") if args.cues else sorted(p.name for p in area_dir.iterdir() if p.is_dir() and p.name != "previews")
    results: list[Result] = []
    for cue in cues:
        seed_dirs = sorted((area_dir / cue).glob("seed*"), key=lambda p: int(p.name[4:]))
        seed_dirs = [d for d in seed_dirs if wanted is None or int(d.name[4:]) in wanted]
        if not seed_dirs:
            results.append(Result("seeds found", f"{area}/{cue}", False, f"no seed directories in {area_dir / cue}"))
            continue
        for d in seed_dirs:
            results += check_midi.check_seed(d)
            results += check_audio.check_seed(d)
        if args.determinism:
            results += check_determinism.check_seed(seed_dirs[0], args.soundfont)
    return results


if __name__ == "__main__":
    sys.exit(main())
