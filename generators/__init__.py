"""Seeded generators, one module per level.

`LEVELS` lists the bundled example levels in order. Private, game-specific generators can
live in `local/generators/` (git-ignored): they are imported as part of this package, so
`make level LEVEL=<name>` works for them too, and they can use `from .common...` imports.
"""

from pathlib import Path

LEVELS = ["meadow", "desert", "tundra", "volcano", "void", "swamp", "reef", "autumn", "crystal", "keep"]

_LOCAL = Path(__file__).resolve().parent.parent / "local" / "generators"
if _LOCAL.is_dir():
    __path__.append(str(_LOCAL))  # noqa: F821 (package __path__)

LOCAL_LEVELS = sorted(p.stem for p in _LOCAL.glob("*.py") if not p.stem.startswith("_")) if _LOCAL.is_dir() else []
AREAS = LEVELS + [a for a in LOCAL_LEVELS if a not in LEVELS]
