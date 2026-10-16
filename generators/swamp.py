"""Level 6, Swamp: humid, murky and a little sinister, with a night-time croak.

G Aeolian. Banjo, muted guitar, clarinet, harmonica, bassoon. Guiro and cuica are the frogs;
vibraphone twinkles are the blinking fireflies.
"""

from .common.arranger import EIGHTHS, FILLS, OFFBEATS, QUARTERS, CueSpec, Kit, LevelSpec, P, V, arrange, module_exports

LEVEL = LevelSpec(
    area="swamp",
    key="G aeolian",
    progressions=[("i", "iv", "i", "v"), ("i", "vi", "v", "i"), ("i", "vii", "iv", "i"), ("i", "iv", "vi", "v")],
    cues={
        "calm": CueSpec(
            bpm=80,
            pads=[
                P("sustain", 20, 48, 72, vel=50, volume=80, name="reed_organ", split=0.25),
                (P("sustain", 49, 48, 72, vel=50, name="low_strings"),
                 P("sparkle", 11, 67, 91, vel=56, name="firefly_vibes", density=0.1, figure="twinkle", length=0.25)),
                P("arp", 105, 52, 79, vel=58, name="banjo_arp", shape=["pendulum", "alberti"], artic=0.5),
                P("strum", 28, 48, 72, vel=52, name="muted_guitar", stagger=12),
            ],
            bass=[P("walk", 35, 28, 55, vel=70, name="fretless_walk"), P("roots", 35, 28, 55, vel=72, name="fretless")],
            percussion=[
                Kit(V(36, (0, 2.5), vel=64), V(73, (1, 3), (1, 2.5, 3), vel=60), V(74, (3.5,), (1.5,), vel=56, prob=0.6),
                    V(70, OFFBEATS, vel=34)),
                Kit(V(78, (1,), (1, 3), vel=56), V(79, (2.5,), vel=50, prob=0.6), V(36, (0,), vel=60), V(76, (0.5, 2, 3.5), vel=40)),
            ],
            lead=[
                P("melody", 71, 55, 79, vel=70, name="clarinet", plan=["breath", "call", "answer"], cells=["sparse", "medium"]),
                P("melody", 22, 60, 84, vel=70, volume=80, name="harmonica", plan=["call", "breath"], cells=["sparse"]),
                P("melody", 70, 46, 72, vel=74, name="bassoon", plan=["breath", "sparse"], cells=["sparse"]),
            ],
            danger=[
                (P("drone", 49, 36, 60, vel=42, name="murk_drone", swell=16),
                 P("sparkle", 117, 40, 60, vel=50, name="frog_toms", density=0.05)),
                P("ostinato", 45, 40, 64, vel=50, name="pizz_creep", rate=1),
            ],
        ),
        "action": CueSpec(
            bpm=100,
            pads=[
                P("stabs", 61, 48, 72, vel=70, name="brass_stabs"),
                P("pulse", 28, 48, 72, vel=64, name="muted_guitar_pulse", artic=0.4),
                P("arp", 105, 52, 79, vel=64, name="banjo_roll", shape=["broken", "pendulum"], rate=0.25, artic=0.5),
            ],
            bass=[P("drive", 34, 28, 55, vel=86, name="pick_bass"), P("walk", 35, 28, 55, vel=82, name="fretless_walk")],
            percussion=[
                Kit(V(36, (0, 1.5, 2.5), (0, 2, 2.75), vel=96), V(38, (1, 3), vel=90), V(73, OFFBEATS, vel=54), V(42, QUARTERS, vel=56),
                    fills=[FILLS["toms"], FILLS["mixed"]], crash=49, kit=8),
                Kit(V(36, (0, 2), vel=96), V(39, (1, 3), vel=86), V(78, (0.5, 2.5), vel=54), V(79, (3.5,), vel=56),
                    V(70, EIGHTHS, vel=46), fills=[FILLS["toms_low"]]),
            ],
            lead=[
                P("melody", 71, 55, 79, vel=84, name="clarinet", plan=["drive", "flow"], cells=["busy", "flowing"]),
                P("melody", 22, 60, 84, vel=82, volume=82, name="harmonica", plan=["drive"], cells=["busy"]),
                P("melody", 66, 50, 77, vel=84, name="tenor_sax", plan=["drive", "answer"], cells=["medium", "busy"]),
            ],
            danger=[
                (P("tremolo", 44, 55, 79, vel=66, name="tremolo_strings", interval=2),
                 P("ostinato", 42, 36, 60, vel=74, name="cello_ostinato"),
                 P("hits", 47, 40, 55, vel=84, name="timpani", bars="odd", roll=True)),
            ],
        ),
    },
    fx={"pads": {"lowpass": 6000}},
)

_e = module_exports(LEVEL)
AREA, KEY, BARS, CUES, STEMS, FX = _e["AREA"], _e["KEY"], _e["BARS"], _e["CUES"], _e["STEMS"], _e["FX"]


def generate(seed, bpm=None, key=None, bars=None, cue=None, motif=None):
    return arrange(LEVEL, seed, bpm, key, bars, cue, motif)
