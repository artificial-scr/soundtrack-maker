from pathlib import Path

import numpy as np
import pytest

from checks.check_audio import SEAM_MAX_RATIO, seam_ratio
from generators import keep, meadow
from generators.common.arranger import make_germ
from generators.common.grid import Grid
from generators.common.motif import load_motif
from generators.common.rng import sub_rng
from generators.common.theory import Key
from render.loop import circular_middle, crossfade_loop

FIXTURE = Path(__file__).parent / "fixtures" / "test_motif.abc"


def test_grid_exact_samples():
    assert Grid(100, 16).samples_per_bar == 115_200
    assert Grid(120, 16).total_samples == 16 * 96_000
    with pytest.raises(ValueError):
        Grid(113, 16)  # 48000*240/113 is not an integer


def test_key_dorian_indices():
    k = Key.parse("D dorian")
    assert k.pitch_classes == (2, 4, 5, 7, 9, 11, 0)
    assert k.pitch(k.index_of(62)) == 62
    assert k.chord("VII").pcs == (0, 4, 7)
    assert k.chord("IV").pcs == (7, 11, 2)


def test_sub_rng_independent_and_stable():
    a = sub_rng(1, "meadow", "lead").random()
    assert a == sub_rng(1, "meadow", "lead").random()
    assert a != sub_rng(1, "meadow", "bass").random()


def test_germ_shared_across_cues_and_varies_by_seed():
    key = Key.parse(meadow.KEY)
    assert make_germ(3, "meadow", key) == make_germ(3, "meadow", key)
    assert len({make_germ(s, "meadow", key) for s in range(1, 30)}) > 10


def test_default_cue_is_first():
    assert meadow.generate(1).cue == next(iter(meadow.CUES))


def test_motif_fixture_drives_lead():
    k = Key.parse(keep.KEY)  # D Aeolian: the fixture's D F A are scale steps 0, 2, 4
    motif = load_motif(FIXTURE, k)
    assert motif.offsets[:3] == (0, 2, 4)
    arr = keep.generate(1, cue="action", motif=motif)
    lead = sorted(arr.stems["lead"][0].notes, key=lambda n: n.start)
    first = [k.index_of(n.pitch) - k.index_of(lead[0].pitch) for n in lead[:3]]
    assert first == [0, 2, 4]


def test_circular_middle_and_crossfade():
    loop = np.random.default_rng(0).normal(size=(1000, 2))
    tiled = np.vstack([loop, loop, loop])
    assert np.array_equal(circular_middle(tiled, 1000), loop)
    out = crossfade_loop(np.ones((48_000 + 4800, 2)), 48_000, 48_000, fade_ms=100)
    assert out.shape == (48_000, 2)
    assert np.allclose(out[0], 1.0, atol=0.05)  # equal-power sum of two correlated 1s stays near 1..1.41


def test_seam_check_detects_click():
    sr = 48_000
    t = np.arange(sr) / sr
    clean = np.sin(2 * np.pi * 100 * t)[:, None].repeat(2, axis=1)  # 100 whole cycles
    clicky = np.sin(2 * np.pi * 100 * t[: sr - 120] + 0.3)[:, None].repeat(2, axis=1)
    clicky = np.vstack([clicky, np.zeros((120, 2))])
    clicky[-1] = 0.0
    clicky[0] = 1.0
    assert seam_ratio(clean) < SEAM_MAX_RATIO
    assert seam_ratio(clicky) > 10 * SEAM_MAX_RATIO


def test_loop_chorus_is_periodic():
    from render.master import loop_chorus

    loop = np.random.default_rng(1).normal(size=(9_600, 2))
    out = loop_chorus(np.vstack([loop, loop, loop]), 48_000, 9_600, rate_hz=0.7, depth=0.3, mix=0.4)
    # Steady state: the 2nd and 3rd copies must be identical (the modulation repeats exactly).
    assert np.allclose(out[9_600:19_200], out[19_200:28_800])
