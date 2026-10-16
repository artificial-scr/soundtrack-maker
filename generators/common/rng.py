"""Seeded RNG helpers. Never use the global `random` module state."""

from __future__ import annotations

import hashlib
import random
from typing import Sequence, TypeVar

T = TypeVar("T")


def sub_rng(seed: int, *labels: str) -> random.Random:
    """Independent RNG per (seed, label...) so changing one stem never reshuffles another.

    Uses sha256 rather than hash(), which varies with PYTHONHASHSEED.
    """
    key = ":".join([str(seed), *labels]).encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest()[:8], "big"))


def weighted_choice(rng: random.Random, options: Sequence[T], weights: Sequence[float]) -> T:
    if len(options) != len(weights) or not options:
        raise ValueError("options and weights must be non-empty and the same length")
    total = sum(weights)
    if total <= 0:
        raise ValueError("weights must sum to a positive value")
    return rng.choices(options, weights=weights, k=1)[0]
