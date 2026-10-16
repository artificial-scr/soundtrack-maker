"""Seed -> MIDI stems -> WAV -> mastered Ogg, for any levels, cues and seeds.

    python -m render.make_stems --list                       # levels, cues, keys, tempos
    python -m render.make_stems --seeds 1-8                  # every level
    python -m render.make_stems --area volcano --cues action --seeds 9-20

Output, per cue and seed:
    stems/{area}/{cue}/seed{N}/{area}_{cue}_{stem}_seed{N}.{mid,wav,ogg}
    stems/{area}/{cue}/seed{N}/build.json
    stems/{area}/previews/{area}_{cue}_mix_seed{N}.ogg   (full mix, for quick auditioning)
"""

from __future__ import annotations

import os

# One numeric-library thread per worker process; the process pool provides the parallelism.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import argparse
import datetime as dt
import hashlib
import importlib
import json
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from importlib.metadata import version
from pathlib import Path

import numpy as np
import soundfile as sf

from generators import AREAS, LEVELS
from generators.common.motif import Motif, load_motif
from generators.common.stems import write_stem
from generators.common.theory import Key
from render import loop, master, render_midi

ROOT = Path(__file__).resolve().parent.parent
STEMS_DIR = ROOT / "stems"
MANIFEST = ROOT / "MANIFEST.md"
OGG_COMPRESSION = 0.4  # libsndfile scale: 0 = best quality; ~0.4 is roughly Vorbis q6


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_seeds(text: str) -> list[int]:
    seeds: list[int] = []
    for chunk in text.split(","):
        if "-" in chunk:
            a, b = chunk.split("-")
            seeds.extend(range(int(a), int(b) + 1))
        else:
            seeds.append(int(chunk))
    return sorted(set(seeds))


JOB_MEMORY_GB = 1.5  # measured peak for the longest loop (60 s) is about 1.2 GB after the limiter fix


def default_jobs() -> int:
    """As many workers as CPUs, but no more than available memory allows."""
    cpus = os.cpu_count() or 1
    try:
        meminfo = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
        available_gb = int(meminfo["MemAvailable"].split()[0]) / 1024**2
    except (OSError, KeyError, ValueError):
        return max(1, cpus // 2)
    return max(1, min(cpus, int(available_gb * 0.8 / JOB_MEMORY_GB)))


def write_ogg(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    """Write Ogg Vorbis in one-second blocks: libsndfile's Vorbis encoder can segfault when
    handed a long buffer (about a minute of stereo) in a single write."""
    with sf.SoundFile(path, "w", samplerate=sample_rate, channels=audio.shape[1], format="OGG",
                      subtype="VORBIS", compression_level=OGG_COMPRESSION) as f:
        for start in range(0, len(audio), sample_rate):
            f.write(audio[start : start + sample_rate])


def stem_name(area: str, cue: str, stem: str, seed: int, ext: str) -> str:
    return f"{area}_{cue}_{stem}_seed{seed}.{ext}"


def build_one(area: str, cue: str, seed: int, out_root: Path, soundfont: Path,
              bpm: int | None = None, key: str | None = None, bars: int | None = None,
              motif_path: Path | None = None, previews: bool = True) -> dict:
    gen = importlib.import_module(f"generators.{area}")
    key = key or gen.KEY
    motif: Motif | None = load_motif(motif_path, Key.parse(key)) if motif_path else None
    arr = gen.generate(seed, bpm=bpm, key=key, bars=bars or gen.BARS, cue=cue, motif=motif)
    grid = arr.grid
    out_dir = out_root / area / cue / f"seed{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)

    dry: dict[str, np.ndarray] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for stem, parts in arr.stems.items():
            write_stem(out_dir / stem_name(area, cue, stem, seed, "mid"), parts, grid)
            looped_mid = Path(tmp) / f"{stem}_x{loop.REPEATS}.mid"
            looped_wav = Path(tmp) / f"{stem}_x{loop.REPEATS}.wav"
            write_stem(looped_mid, parts, grid, repeats=loop.REPEATS)
            render_midi.render(looped_mid, looped_wav, soundfont, grid.sample_rate)
            audio = render_midi.read_exact(looped_wav, loop.REPEATS * grid.total_samples)
            audio = master.apply_fx(stem, audio, grid.sample_rate, getattr(gen, "FX", {}).get(stem), grid.bpm,
                                    grid.total_samples)
            dry[stem] = loop.circular_middle(audio, grid.total_samples)

    mastered, report = master.master(dry, grid.sample_rate)
    for stem, audio in mastered.items():
        sf.write(out_dir / stem_name(area, cue, stem, seed, "wav"), audio, grid.sample_rate, subtype="PCM_24")
        write_ogg(out_dir / stem_name(area, cue, stem, seed, "ogg"), audio, grid.sample_rate)
    if previews:
        preview_dir = out_root / area / "previews"
        preview_dir.mkdir(parents=True, exist_ok=True)
        write_ogg(preview_dir / f"{area}_{cue}_mix_seed{seed}.ogg", sum(mastered.values()), grid.sample_rate)

    meta = arr.metadata()
    meta.update({
        "motif": motif.source if motif else "seed germ",
        "master": report,
        "soundfont": {"file": soundfont.name, "sha256": sha256(soundfont)},
        "generator_sha256": sha256(Path(gen.__file__)),
        "tools": {
            "fluidsynth": render_midi.fluidsynth_version(),
            **{pkg: version(pkg) for pkg in ("pedalboard", "pyloudnorm", "soundfile", "mido", "numpy", "scipy")},
        },
    })
    (out_dir / "build.json").write_text(json.dumps(meta, indent=2) + "\n")
    return {"area": area, "cue": cue, "seed": seed, "dir": str(out_dir.relative_to(ROOT)) if out_dir.is_relative_to(ROOT) else str(out_dir), **report}


def log_manifest(area: str, cues: list[str], seeds: list[int], soundfont: Path, args: argparse.Namespace) -> None:
    gen = importlib.import_module(f"generators.{area}")
    stamp = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    seed_text = f"{seeds[0]}-{seeds[-1]}" if seeds == list(range(seeds[0], seeds[-1] + 1)) else ",".join(map(str, seeds))
    lines = [
        f"- {stamp}: `{area}` cues {', '.join(cues)}, seeds {seed_text}; "
        f"key {args.key or gen.KEY}, bars {args.bars or gen.BARS}, bpm {args.bpm or 'cue default'}; "
        f"motif {args.motif or 'seed germ'}; soundfont {soundfont.name} ({sha256(soundfont)[:12]}); "
        f"generator sha256 {sha256(Path(gen.__file__))[:12]}; no audio models, no prompts.",
    ]
    with MANIFEST.open("a") as f:
        f.write("\n".join(lines) + "\n")


def list_levels() -> int:
    print(f"{'level':<9} {'key':<13} {'bars':>4}  cues (BPM)")
    for area in AREAS:
        gen = importlib.import_module(f"generators.{area}")
        cues = ", ".join(f"{c} ({v['bpm']})" for c, v in gen.CUES.items())
        note = "  [local]" if area not in LEVELS else ""
        print(f"{area:<9} {gen.KEY:<13} {gen.BARS:>4}  {cues}{note}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--area", default="all", help="level name, comma-separated list, or 'all' (every level)")
    ap.add_argument("--cues", default=None, help="comma-separated; default: all cues of the area")
    ap.add_argument("--seeds", default="1-8")
    ap.add_argument("--bpm", type=int, default=None, help="override the cue's default tempo")
    ap.add_argument("--key", default=None)
    ap.add_argument("--bars", type=int, default=None)
    ap.add_argument("--motif", type=Path, default=None, help="MIDI or ABC file in motifs/")
    ap.add_argument("--soundfont", type=Path, default=render_midi.DEFAULT_SOUNDFONT)
    ap.add_argument("--out", type=Path, default=STEMS_DIR)
    ap.add_argument("--jobs", type=int, default=None, help="worker processes (default: limited by CPUs and free memory)")
    ap.add_argument("--no-manifest", action="store_true")
    ap.add_argument("--list", action="store_true", help="list levels and their cues, then exit")
    args = ap.parse_args(argv)
    if args.list:
        return list_levels()

    areas = LEVELS if args.area == "all" else args.area.split(",")
    unknown = [a for a in areas if a not in AREAS]
    if unknown:
        ap.error(f"unknown level(s) {', '.join(unknown)}; choose from: {', '.join(AREAS)} (or 'all')")
    seeds = parse_seeds(args.seeds)
    jobs = []
    for area in areas:
        gen = importlib.import_module(f"generators.{area}")
        cues = args.cues.split(",") if args.cues else list(gen.CUES)
        jobs += [(area, cue, seed) for seed in seeds for cue in cues if cue in gen.CUES]

    results = []
    with ProcessPoolExecutor(max_workers=args.jobs or default_jobs()) as pool:
        futures = [
            pool.submit(build_one, area, cue, seed, args.out, args.soundfont, args.bpm, args.key, args.bars, args.motif)
            for area, cue, seed in jobs
        ]
        for fut in futures:
            r = fut.result()
            results.append(r)
            print(f"{r['area']:>8} {r['cue']:>6} seed{r['seed']:<4} {r['mix_lufs']:6.2f} LUFS  {r['mix_true_peak_dbtp']:6.2f} dBTP  "
                  f"limiter max {r['max_limiter_reduction_db']:.1f} dB  -> {r['dir']}")
    if not args.no_manifest:
        for area in areas:
            gen = importlib.import_module(f"generators.{area}")
            cues = [c for c in (args.cues.split(",") if args.cues else gen.CUES) if c in gen.CUES]
            log_manifest(area, cues, seeds, args.soundfont, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
