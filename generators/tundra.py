"""Level 3, Tundra: cold, quiet and spacious, a hushed snowfall.

F# Aeolian, slow (75 BPM). Bowed glass, choir and harp; Ice Rain and music box for falling
snow; long reverb. Percussion is almost absent in the calm cue.
"""

from .common.arranger import EIGHTHS, FILLS, CueSpec, Kit, LevelSpec, P, V, arrange, module_exports

LEVEL = LevelSpec(
    area="tundra",
    key="F# aeolian",
    progressions=[("i", "vi", "iii", "vii"), ("i", "iv", "vi", "v"), ("vi", "vii", "i", "i"), ("i", "vii", "vi", "vii")],
    cues={
        "calm": CueSpec(
            bpm=75,
            pads=[
                P("sustain", 92, 54, 78, vel=58, name="bowed_glass", swell=[16, 32]),
                (P("sustain", 52, 55, 76, vel=50, name="choir"),
                 P("sparkle", 96, 72, 96, vel=55, name="ice_rain", density=[0.06, 0.1], length=1.0)),
                P("arp", 46, 48, 84, vel=55, name="harp", shape=["up", "updown"], span=[5, 6]),
            ],
            bass=[
                P("bass_sustain", 43, 28, 55, vel=60, name="double_bass"),
                P("roots", 43, 28, 55, vel=60, name="double_bass", patterns=(((0, "R", 4),), ((0, "R", 2), (2, "5", 2)))),
            ],
            percussion=[
                Kit(V(81, (0,), (2,), vel=40, prob=0.5), V(53, (1, 3), vel=34, prob=0.4), kit=48),
                Kit(V(80, (0, 1.5, 3), vel=36, prob=0.6), V(36, (0,), vel=50), kit=48),
            ],
            lead=[
                P("melody", 10, 64, 88, vel=66, name="music_box", plan=["sparse"], cells=["long", "sparse"], echo=[0, 1.5]),
                P("melody", 73, 60, 84, vel=62, volume=78, name="flute", plan=["sparse", "breath"], cells=["long"]),
                P("melody", 98, 64, 88, vel=64, name="crystal", plan=["sparse"], cells=["long", "sparse"]),
            ],
            danger=[
                P("drone", 49, 36, 60, vel=40, name="low_strings", swell=16),
                P("texture", 95, 40, 64, vel=50, name="sweep", swell=16),
            ],
        ),
        "action": CueSpec(
            bpm=100,
            pads=[
                P("pulse", 49, 54, 78, vel=58, name="string_pulse", rate=1, artic=0.9),
                P("arp", 8, 60, 90, vel=58, name="celesta_arp", shape=["updown", "pendulum"], rate=0.25),
                P("stabs", 48, 54, 76, vel=64, name="string_stabs", rhythms=[[(0, 1.5, 3), (0, 2)]]),
            ],
            bass=[
                P("drive", 43, 28, 55, vel=74, name="double_bass", artic=0.6),
                P("roots", 43, 28, 55, vel=74, name="double_bass"),
            ],
            percussion=[
                Kit(V(36, (0, 2.5), vel=86), V(38, (1, 3), vel=70), V(42, EIGHTHS, vel=46), fills=[FILLS["half"]], kit=48),
                Kit(V(36, (0, 2), vel=90), V(40, (1, 3), vel=74), V(81, (0,), vel=50), fills=[FILLS["toms_low"]], kit=8),
            ],
            lead=[
                P("melody", 73, 62, 86, vel=80, name="flute", plan=["flow", "answer"], cells=["flowing", "medium"]),
                P("melody", 40, 60, 86, vel=80, name="violin", plan=["drive", "flow"], cells=["medium", "flowing"]),
                P("melody", 98, 64, 88, vel=80, name="crystal", plan=["answer"], cells=["medium"], echo=0.75),
            ],
            danger=[
                (P("tremolo", 44, 60, 84, vel=66, name="tremolo_strings"),
                 P("hits", 47, 40, 55, vel=82, name="timpani", bars="odd", roll=True)),
                (P("ostinato", 45, 48, 72, vel=72, name="pizz"),
                 P("texture", 95, 40, 64, vel=60, name="sweep", swell=8)),
            ],
        ),
    },
    fx={
        "pads": {"reverb": (0.88, 0.32)},
        "lead": {"reverb": (0.85, 0.3)},
        "danger": {"reverb": (0.88, 0.3)},
    },
)

_e = module_exports(LEVEL)
AREA, KEY, BARS, CUES, STEMS, FX = _e["AREA"], _e["KEY"], _e["BARS"], _e["CUES"], _e["STEMS"], _e["FX"]


def generate(seed, bpm=None, key=None, bars=None, cue=None, motif=None):
    return arrange(LEVEL, seed, bpm, key, bars, cue, motif)
