import importlib

import pytest

from generators import LEVELS
from generators.common.arranger import STEMS
from generators.common.stems import stem_midi

SEEDS = range(1, 26)


def _cases():
    for level in LEVELS:
        gen = importlib.import_module(f"generators.{level}")
        for cue in gen.CUES:
            yield level, cue


@pytest.mark.parametrize("level,cue", list(_cases()))
def test_level_invariants(level, cue):
    gen = importlib.import_module(f"generators.{level}")
    for seed in SEEDS:
        arr = gen.generate(seed, cue=cue)
        key_pcs = set(arr.key.pitch_classes)
        assert list(arr.stems) == STEMS
        for stem, parts in arr.stems.items():
            assert parts, f"{level}/{cue}/seed{seed}: {stem} has no parts"
            assert len({p.name for p in parts}) == len(parts), "track names must be unique per stem"
            for part in parts:
                assert part.notes, f"{level}/{cue}/seed{seed}: {stem}:{part.name} is empty"
                for n in part.notes:
                    assert 0 <= n.start and n.end <= arr.grid.total_ticks, (level, cue, seed, part.name, n)
                    assert part.lo <= n.pitch <= part.hi, (level, cue, seed, part.name, n)
                    if not part.drums:
                        assert n.pitch % 12 in key_pcs, (level, cue, seed, part.name, n)
                if part.monophonic:
                    ordered = sorted(part.notes, key=lambda n: n.start)
                    assert all(a.end <= b.start for a, b in zip(ordered, ordered[1:])), (level, cue, seed, part.name)
            stem_midi(parts, arr.grid)


@pytest.mark.parametrize("level", LEVELS)
def test_seeds_vary(level):
    """Different seeds should pick different recipes, not just different notes."""
    gen = importlib.import_module(f"generators.{level}")
    signatures = set()
    for seed in range(1, 13):
        arr = gen.generate(seed)  # first cue
        signatures.add((tuple(arr.chords[:8]),) + tuple(tuple(p.name for p in arr.stems[s]) for s in STEMS))
    assert len(signatures) >= 6, f"{level}: only {len(signatures)} distinct arrangements in 12 seeds"


@pytest.mark.parametrize("level", LEVELS)
def test_level_deterministic(level):
    gen = importlib.import_module(f"generators.{level}")
    for cue in gen.CUES:
        a, b = gen.generate(3, cue=cue), gen.generate(3, cue=cue)
        assert [[p.notes for p in a.stems[s]] for s in STEMS] == [[p.notes for p in b.stems[s]] for s in STEMS]
