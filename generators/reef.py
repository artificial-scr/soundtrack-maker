"""Level 7, Coral Reef: underwater, buoyant and colourful; muffled and flowing.

A Mixolydian. Marimba and harp arpeggios, steel drum, vibraphone and pan flute leads,
kalimba "bubbles" that rise. Low-pass filtering and chorus give the underwater muffle.
"""

from .common.arranger import EIGHTHS, FILLS, OFFBEATS, SIXTEENTHS, CueSpec, Kit, LevelSpec, P, V, arrange, module_exports

LEVEL = LevelSpec(
    area="reef",
    key="A mixolydian",
    progressions=[("I", "vii", "IV", "I"), ("I", "v", "IV", "I"), ("I", "IV", "vii", "IV"), ("I", "ii", "IV", "I")],
    cues={
        "calm": CueSpec(
            bpm=96,
            pads=[
                P("arp", 12, 55, 84, vel=60, name="marimba_arp", shape=["up", "updown", "broken"], span=[5, 6]),
                (P("sustain", 89, 55, 79, vel=50, name="warm_pad"),
                 P("sparkle", 108, 67, 91, vel=54, name="kalimba_bubbles", density=0.1, figure="rise")),
                P("arp", 46, 48, 84, vel=56, name="harp_flow", shape="updown", span=6),
            ],
            bass=[P("roots", 32, 28, 55, vel=74, name="acoustic_bass"), P("walk", 35, 28, 55, vel=70, name="fretless")],
            percussion=[
                Kit(V(64, (0, 2), (0, 1.5, 2.5), vel=60), V(63, (1, 3), (1, 2.75), vel=52), V(69, EIGHTHS, vel=32),
                    V(75, (1.5, 3.5), vel=40, prob=0.5)),
                Kit(V(36, (0, 2.5), vel=60), V(70, OFFBEATS, vel=36), V(81, (0,), vel=34, prob=0.5)),
            ],
            lead=[
                P("melody", 114, 60, 86, vel=70, name="steel_drum", plan=["breath", "answer"], cells=["sparse", "medium"]),
                P("melody", 11, 60, 86, vel=70, name="vibraphone", plan=["breath", "call"], cells=["medium"], echo=[0, 0.75]),
                P("melody", 75, 62, 86, vel=68, name="pan_flute", plan=["breath", "answer"], cells=["sparse"]),
            ],
            danger=[
                P("drone", 49, 36, 60, vel=42, name="deep_strings", swell=16),
                P("texture", 122, 40, 64, vel=50, name="sea", swell=16),
            ],
        ),
        "action": CueSpec(
            bpm=120,
            pads=[
                P("arp", 12, 55, 84, vel=66, name="marimba_run", shape=["up", "pendulum"], rate=0.25),
                P("stabs", 61, 52, 76, vel=70, name="brass_stabs"),
                P("pulse", 11, 55, 79, vel=62, name="vibes_pulse", artic=0.5),
            ],
            bass=[P("drive", 36, 28, 55, vel=84, name="slap_bass"), P("drive", 33, 28, 55, vel=84, name="finger_bass")],
            percussion=[
                Kit(V(36, (0, 1.5, 2.5), vel=96), V(38, (1, 3), vel=86), V(42, EIGHTHS, vel=58), V(63, (0.75, 2.75), vel=60),
                    fills=[FILLS["toms"], FILLS["mixed"]], crash=49),
                Kit(V(36, (0, 2), vel=96), V(39, (1, 3), vel=84), V(62, OFFBEATS, vel=60), V(64, (1.75, 3.25), vel=64),
                    V(69, SIXTEENTHS, vel=36, accent=12), fills=[FILLS["toms_low"]]),
            ],
            lead=[
                P("melody", 114, 60, 86, vel=84, name="steel_drum", plan=["drive", "flow"], cells=["busy", "flowing"]),
                P("melody", 56, 58, 82, vel=84, name="trumpet", plan=["drive"], cells=["medium", "busy"]),
                P("melody", 80, 60, 84, vel=84, name="square_lead", plan=["flow"], cells=["flowing"]),
            ],
            danger=[
                (P("tremolo", 44, 60, 84, vel=64, name="tremolo_strings"),
                 P("ostinato", 45, 48, 72, vel=70, name="pizz_ostinato"),
                 P("hits", 47, 40, 55, vel=80, name="timpani", bars="odd", roll=True)),
            ],
        ),
    },
    fx={
        "pads": {"lowpass": 3200, "chorus": (0.6, 0.25, 0.3), "reverb": (0.7, 0.25)},
        "lead": {"lowpass": 4500, "chorus": (0.5, 0.2, 0.25)},
        "percussion": {"lowpass": 6000},
        "danger": {"lowpass": 2500},
    },
)

_e = module_exports(LEVEL)
AREA, KEY, BARS, CUES, STEMS, FX = _e["AREA"], _e["KEY"], _e["BARS"], _e["CUES"], _e["STEMS"], _e["FX"]


def generate(seed, bpm=None, key=None, bars=None, cue=None, motif=None):
    return arrange(LEVEL, seed, bpm, key, bars, cue, motif)
