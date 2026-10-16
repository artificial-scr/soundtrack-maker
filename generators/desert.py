"""Level 2, Desert: hot, dry and windswept, with constant forward drive.

E Phrygian (the flat second gives the heat). Tonic pedal bass and hand drums keep it moving
even in the calm cue; shenai, oboe and sitar leads; wind (Seashore) swells in the danger layer.
"""

from .common.arranger import EIGHTHS, FILLS, SIXTEENTHS, CueSpec, Kit, LevelSpec, P, V, arrange, module_exports

LEVEL = LevelSpec(
    area="desert",
    key="E phrygian",
    progressions=[("i", "ii", "i", "vii"), ("i", "vii", "vi", "vii"), ("i", "iv", "ii", "i"), ("i", "i", "ii", "ii")],
    cues={
        "calm": CueSpec(
            bpm=100,
            pads=[
                P("arp", 24, 52, 76, vel=60, name="nylon_arp", shape=["pendulum", "broken", "updown"]),
                P("sustain", 50, 55, 76, vel=52, name="synth_strings", swell=[8, 16]),
                (P("sustain", 49, 52, 74, vel=50, name="strings"),
                 P("sparkle", 107, 64, 88, vel=60, name="koto_glints", density=0.1, figure="fall")),
            ],
            bass=[
                P("pedal", 35, 28, 55, vel=76, name="fretless_pedal", rhythm=[(0, 1.5, 2, 3.5), (0, 0.75, 1.5, 2, 3)], length=0.6),
                P("roots", 35, 28, 55, vel=78, name="fretless"),
            ],
            percussion=[
                Kit(V(64, (0, 1.5, 2, 3), (0, 0.75, 2, 2.5), vel=70), V(62, (1, 2.5, 3.5), (1, 3), vel=56),
                    V(63, (0.5, 2.75), vel=50, prob=0.8), V(69, EIGHTHS, vel=34)),
                Kit(V(60, (0, 0.75, 1.5, 2, 2.75, 3.5), vel=58), V(61, (1, 3), vel=62), V(54, (0.5, 1.5, 2.5, 3.5), vel=42)),
            ],
            lead=[
                P("melody", 111, 62, 84, vel=70, volume=70, name="shenai", plan=["breath", "call"], cells=["sparse", "medium"]),
                P("melody", 68, 62, 86, vel=72, volume=85, name="oboe", plan=["breath", "answer"]),
                P("melody", 104, 60, 84, vel=78, name="sitar", plan=["call", "answer"], cells=["medium"]),
            ],
            danger=[
                (P("texture", 122, 40, 64, vel=60, volume=90, name="wind", swell=8),
                 P("hits", 116, 36, 55, vel=60, name="taiko", bars="phrase")),
                # Breath Noise (121) renders 25-30 dB quieter than Seashore in GeneralUser GS: inaudible.
                (P("texture", 122, 52, 76, vel=58, name="high_wind", swell=16),
                 P("drone", 50, 40, 64, vel=40, name="heat_drone", swell=16)),
            ],
        ),
        "action": CueSpec(
            bpm=128,
            pads=[
                P("pulse", 48, 52, 76, vel=64, name="string_pulse", artic=0.45, accents=(0, 1.5, 3)),
                P("stabs", 61, 52, 74, vel=70, name="brass_stabs", rhythms=[[(0, 0.75, 1.5, 3), (0, 1.5, 3)]]),
                P("arp", 104, 52, 79, vel=62, name="sitar_arp", shape=["pendulum", "broken"], rate=0.25, artic=0.6),
            ],
            bass=[
                P("pedal", 38, 28, 55, vel=86, name="synth_bass_pedal", octaves=[True, False], rhythm=EIGHTHS, length=0.4),
                P("drive", 33, 28, 55, vel=86, name="finger_bass"),
            ],
            percussion=[
                Kit(V(36, (0, 1.5, 2, 3), (0, 0.75, 2, 2.75), vel=100), V(38, (1, 3), vel=90), V(64, (0.5, 1.25, 2.5, 3.25), vel=70),
                    V(69, SIXTEENTHS, vel=40, accent=14), fills=[FILLS["toms"], FILLS["toms_low"]]),
                Kit(V(36, (0, 2.5), (0, 1.5, 2.5), vel=98), V(39, (1, 3), vel=86), V(62, (0.5, 1.5, 2.75), vel=66),
                    V(63, (1.25, 3.5), vel=62), V(54, EIGHTHS, vel=50), fills=[FILLS["toms"], FILLS["half"]], crash=49),
            ],
            lead=[
                P("melody", 111, 62, 84, vel=82, volume=78, name="shenai", plan=["drive", "flow"], cells=["busy", "flowing"]),
                P("melody", 81, 60, 84, vel=84, volume=85, name="saw_lead", plan=["drive"], cells=["busy"]),
                P("melody", 104, 60, 84, vel=88, name="sitar", plan=["flow", "drive"], cells=["flowing"]),
            ],
            danger=[
                (P("ostinato", 45, 48, 72, vel=80, name="pizz_ostinato", rate=0.25),
                 P("hits", 116, 36, 55, vel=92, name="taiko", bars="every", beats=(0, 1.5, 2.5), length=0.5, roll=True),
                 P("texture", 122, 40, 64, vel=70, name="wind", swell=8)),
            ],
        ),
    },
    fx={"danger": {"reverb": (0.5, 0.15)}},
)

_e = module_exports(LEVEL)
AREA, KEY, BARS, CUES, STEMS, FX = _e["AREA"], _e["KEY"], _e["BARS"], _e["CUES"], _e["STEMS"], _e["FX"]


def generate(seed, bpm=None, key=None, bars=None, cue=None, motif=None):
    return arrange(LEVEL, seed, bpm, key, bars, cue, motif)
