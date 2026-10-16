"""Level 8, Autumn: warm, nostalgic and melancholic, with a harvest feel.

B Aeolian. Nylon guitar, accordion and harp; oboe, clarinet, harmonica or cello leads;
brush and jazz kits in the calm cue, fiddle and violin in the action cue.
"""

from .common.arranger import EIGHTHS, FILLS, CueSpec, Kit, LevelSpec, P, V, arrange, module_exports

LEVEL = LevelSpec(
    area="autumn",
    key="B aeolian",
    progressions=[("i", "vi", "iii", "vii"), ("i", "iv", "vii", "iii"), ("vi", "vii", "i", "i"), ("i", "iii", "vii", "iv"),
                  ("i", "vi", "iii", "vii", "i", "iv", "v", "i")],
    cues={
        "calm": CueSpec(
            bpm=80,
            pads=[
                P("arp", 24, 48, 79, vel=60, name="nylon_arp", shape=["up", "alberti", "broken"], span=[5, 6]),
                P("sustain", 21, 52, 76, vel=52, volume=80, name="accordion", split=0.3),
                (P("sustain", 49, 52, 74, vel=50, name="strings"),
                 P("arp", 46, 55, 84, vel=46, name="harp", shape="updown", rate=1, span=5)),
            ],
            bass=[P("roots", 32, 28, 55, vel=74, name="acoustic_bass"), P("walk", 32, 28, 55, vel=70, name="acoustic_bass")],
            percussion=[
                Kit(V(36, (0, 2), vel=60), V(38, (1, 3), vel=46), V(44, (1, 3), vel=40), kit=40),
                Kit(V(36, (0, 2.5), vel=58), V(37, (1, 3), vel=44), V(70, EIGHTHS, vel=30), kit=32),
            ],
            lead=[
                P("melody", 68, 62, 86, vel=70, name="oboe", plan=["breath", "answer"], cells=["sparse", "medium"]),
                P("melody", 71, 55, 79, vel=70, name="clarinet", plan=["breath", "call"], cells=["sparse"]),
                P("melody", 22, 60, 84, vel=66, volume=78, name="harmonica", plan=["answer", "breath"], cells=["medium"]),
                P("melody", 42, 48, 74, vel=72, name="cello", plan=["breath"], cells=["sparse", "long"]),
            ],
            danger=[
                (P("drone", 49, 36, 60, vel=42, name="low_strings", swell=16),
                 P("hits", 47, 40, 55, vel=52, name="timpani", bars="phrase")),
                P("tremolo", 44, 60, 84, vel=44, name="soft_tremolo"),
            ],
        ),
        "action": CueSpec(
            bpm=100,
            pads=[
                P("strum", 25, 48, 74, vel=64, name="steel_strum"),
                P("stabs", 48, 52, 76, vel=70, name="string_stabs"),
                P("arp", 24, 48, 79, vel=66, name="nylon_run", shape=["broken", "pendulum"], rate=0.25),
            ],
            bass=[P("drive", 33, 28, 55, vel=84, name="finger_bass"), P("walk", 32, 28, 55, vel=80, name="acoustic_bass")],
            percussion=[
                Kit(V(36, (0, 2), (0, 1.5, 2), vel=94), V(38, (1, 3), vel=84), V(42, EIGHTHS, vel=56),
                    fills=[FILLS["snare16"], FILLS["toms"]], crash=49, kit=8),
                Kit(V(36, (0, 2.5), vel=90), V(38, (1, 3), vel=80), V(51, (0, 1, 1.5, 2, 3, 3.5), vel=54),
                    fills=[FILLS["mixed"]], crash=57, kit=40),
            ],
            lead=[
                P("melody", 40, 60, 86, vel=82, name="violin", plan=["drive", "flow"], cells=["medium", "flowing"]),
                P("melody", 68, 62, 86, vel=80, name="oboe", plan=["drive", "answer"], cells=["medium"]),
                P("melody", 110, 60, 86, vel=82, name="fiddle", plan=["flow", "drive"], cells=["flowing", "busy"]),
            ],
            danger=[
                (P("tremolo", 44, 60, 84, vel=66, name="tremolo_strings"),
                 P("ostinato", 42, 36, 60, vel=72, name="cello_ostinato"),
                 P("hits", 47, 40, 55, vel=82, name="timpani", bars="odd", roll=True)),
            ],
        ),
    },
)

_e = module_exports(LEVEL)
AREA, KEY, BARS, CUES, STEMS, FX = _e["AREA"], _e["KEY"], _e["BARS"], _e["CUES"], _e["STEMS"], _e["FX"]


def generate(seed, bpm=None, key=None, bars=None, cue=None, motif=None):
    return arrange(LEVEL, seed, bpm, key, bars, cue, motif)
