"""Shared types for validation checks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Result:
    check: str
    target: str
    ok: bool
    detail: str = ""

    def __post_init__(self) -> None:
        self.ok = bool(self.ok)  # numpy bools are not JSON serializable

    def line(self) -> str:
        return f"[{'PASS' if self.ok else 'FAIL'}] {self.check:<22} {self.target:<34} {self.detail}"


def load_build(seed_dir: Path) -> dict:
    return json.loads((seed_dir / "build.json").read_text())


def stem_files(seed_dir: Path, meta: dict, ext: str) -> dict[str, Path]:
    return {
        stem: seed_dir / f"{meta['area']}_{meta['cue']}_{stem}_seed{meta['seed']}.{ext}"
        for stem in meta["stems"]
    }
