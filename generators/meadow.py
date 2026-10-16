"""Level 1, Meadow: pastoral and bright, a gentle opening-level calm.

G major. Nylon guitar, flute, ocarina, recorder; glockenspiel glints for drifting pollen.
"""

from .common.arranger import EIGHTHS, FILLS, OFFBEATS, CueSpec, Kit, LevelSpec, P, V, arrange, module_exports

LEVEL = LevelSpec(
    area="meadow",
    key="G ionian",
    progressions=[("I", "V", "vi", "IV"), ("I", "IV", "I", "V"), ("I", "vi", "IV", "V"),
                  ("I", "iii", "IV", "V", "vi", "IV", "ii", "V")],
    cues={
        "calm": CueSpec(
            bpm=100,
            pads=[
                P("arp", 24, 52, 79, vel=62, name="nylon_arp", shape=["up", "updown", "alberti", "broken"], span=[4, 5, 6]),
                P("sustain", 49, 55, 76, vel=56, name="slow_strings", split=[0.0, 0.3]),
                (P("sustain", 89, 55, 76, vel=52, name="warm_pad"),
                 P("sparkle", 9, 79, 96, vel=56, name="glock_pollen", density=[0.08, 0.12], figure=["single", "rise"])),
                P("strum", 25, 50, 74, vel=54, name="steel_strum", rhythms=[[(0, 1.5, 2, 3), (0, 2, 2.5, 3.5)]]),
            ],
            bass=[P("roots", 32, 28, 55, vel=80, name="acoustic_bass"), P("walk", 32, 28, 55, vel=76, name="acoustic_bass")],
            percussion=[
                Kit(V(36, (0, 2), (0, 2.5), vel=70), V(70, EIGHTHS, vel=38, accent=10), V(37, (1, 3), vel=48, prob=0.9), kit=8),
                Kit(V(36, (0, 2), vel=66), V(54, (1, 3), (1, 2.5, 3), vel=50), V(42, OFFBEATS, vel=40)),
                Kit(V(75, (0, 1.5, 3), (0, 1, 2.5), vel=55), V(70, EIGHTHS, vel=36), V(64, (2, 3.5), vel=58)),
            ],
            lead=[
                P("melody", 73, 62, 86, vel=72, volume=80, name="flute", plan=["breath", "call", "answer"], cells=["sparse", "medium"], artic=0.92),
                P("melody", 79, 62, 86, vel=74, volume=85, name="ocarina", plan=["breath", "call"], cells=["sparse", "medium"]),
                P("melody", 74, 64, 88, vel=70, volume=82, name="recorder", plan=["answer", "breath"], cells=["medium"], echo=[0, 0.75]),
            ],
            danger=[
                (P("drone", 49, 36, 60, vel=44, volume=80, name="low_strings"),
                 P("hits", 47, 40, 55, vel=56, name="timpani", bars="odd", roll=True)),
                P("tremolo", 44, 60, 84, vel=46, name="soft_tremolo"),
            ],
        ),
        "action": CueSpec(
            bpm=120,
            pads=[
                P("stabs", 48, 52, 76, vel=76, name="string_stabs"),
                P("strum", 25, 50, 74, vel=70, name="steel_strum"),
                P("pulse", 48, 52, 76, vel=64, name="string_pulse", artic=0.5),
            ],
            bass=[P("drive", 33, 28, 55, vel=86, name="finger_bass"), P("roots", 33, 28, 55, vel=86, name="finger_bass", artic=0.7)],
            percussion=[
                Kit(V(36, (0, 2), (0, 1.5, 2), (0, 2, 2.5), vel=100), V(38, (1, 3), vel=96), V(42, EIGHTHS, vel=66, accent=12),
                    fills=[FILLS["snare16"], FILLS["toms"], FILLS["mixed"]], crash=49),
                Kit(V(36, (0, 1.5, 2), vel=98), V(38, (1, 3), vel=92), V(54, EIGHTHS, vel=58),
                    fills=[FILLS["toms"], FILLS["half"]], crash=49, kit=8),
            ],
            lead=[
                P("melody", 72, 64, 88, vel=84, volume=80, name="piccolo", plan=["drive", "flow"], cells=["busy", "flowing"]),
                P("melody", 80, 60, 84, vel=86, volume=100, name="square_lead", plan=["drive"], cells=["busy"]),
                P("melody", 56, 58, 82, vel=86, volume=90, name="trumpet", plan=["drive", "answer"], cells=["medium", "busy"]),
            ],
            danger=[
                (P("tremolo", 44, 60, 84, vel=70, name="tremolo_strings"),
                 P("ostinato", 42, 36, 60, vel=76, name="cello_ostinato"),
                 P("hits", 47, 40, 55, vel=88, name="timpani", bars="every", roll=True)),
            ],
        ),
    },
)

_e = module_exports(LEVEL)
AREA, KEY, BARS, CUES, STEMS, FX = _e["AREA"], _e["KEY"], _e["BARS"], _e["CUES"], _e["STEMS"], _e["FX"]


def generate(seed, bpm=None, key=None, bars=None, cue=None, motif=None):
    return arrange(LEVEL, seed, bpm, key, bars, cue, motif)
