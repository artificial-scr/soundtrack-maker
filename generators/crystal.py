"""Level 9, Crystal Caves: mysterious and glittering; bells and celesta.

E Lydian. Bowed glass and fantasia pads with celesta and glockenspiel glints that pop in
and out; music box and celesta arpeggios; tubular bells; long reverb with a little delay.
"""

from .common.arranger import EIGHTHS, FILLS, CueSpec, Kit, LevelSpec, P, V, arrange, module_exports

LEVEL = LevelSpec(
    area="crystal",
    key="E lydian",
    progressions=[("I", "II", "I", "II"), ("vi", "II", "I", "I"), ("I", "iii", "II", "vii"), ("I", "V", "vi", "II")],
    cues={
        "calm": CueSpec(
            bpm=80,
            pads=[
                (P("sustain", 92, 55, 79, vel=52, name="bowed_glass", swell=16),
                 P("sparkle", 8, 72, 96, vel=58, name="celesta_glints", density=[0.1, 0.15], rate=0.25, figure=["single", "twinkle"], length=0.25)),
                P("arp", 10, 64, 91, vel=58, name="music_box_arp", shape=["up", "pendulum", "updown"], span=6),
                (P("sustain", 88, 55, 79, vel=52, name="fantasia"),
                 P("sparkle", 9, 79, 100, vel=52, name="glock_glints", density=0.08, rate=0.25, length=0.25)),
            ],
            bass=[
                P("bass_sustain", 35, 28, 55, vel=62, name="fretless"),
                P("roots", 43, 28, 55, vel=62, name="double_bass",
                  patterns=(((0, "R", 4),), ((0, "R", 2), (2, "5", 2)), ((0, "R", 3), (3, "APP", 1)))),
            ],
            percussion=[
                Kit(V(81, (0,), (0, 2), vel=40), V(80, (1, 3), (1.5, 3.5), vel=34, prob=0.7), kit=48),
                Kit(V(36, (0,), vel=56), V(53, (2,), vel=36), V(75, (1.5, 3.5), vel=38, prob=0.6)),
            ],
            lead=[
                P("melody", 8, 64, 91, vel=66, name="celesta", plan=["breath", "call", "sparse"], cells=["sparse", "medium"], echo=[0, 0.75]),
                P("melody", 14, 60, 84, vel=60, name="tubular_bells", plan=["sparse"], cells=["long"]),
                P("melody", 98, 64, 88, vel=64, name="crystal", plan=["breath", "sparse"], cells=["sparse"]),
            ],
            danger=[
                P("drone", 92, 36, 60, vel=44, name="glass_drone", swell=16),
                P("texture", 99, 40, 64, vel=48, name="atmosphere", swell=16),
            ],
        ),
        "action": CueSpec(
            bpm=120,
            pads=[
                P("arp", 8, 64, 91, vel=62, name="celesta_run", shape=["up", "pendulum", "broken"], rate=0.25, span=6),
                P("pulse", 11, 55, 79, vel=60, name="vibes_pulse", artic=0.5),
                (P("stabs", 48, 52, 76, vel=66, name="string_stabs"),
                 P("sparkle", 9, 79, 100, vel=58, name="glock_glints", density=0.15, rate=0.25, length=0.25)),
            ],
            bass=[P("drive", 38, 28, 55, vel=82, name="synth_bass"), P("drive", 35, 28, 55, vel=80, name="fretless", artic=0.6)],
            percussion=[
                Kit(V(36, (0, 2), (0, 1.5, 2.5), vel=96), V(38, (1, 3), vel=84), V(80, EIGHTHS, vel=48, accent=12), V(81, (3.5,), vel=56),
                    fills=[FILLS["toms"], FILLS["half"]], crash=49),
                Kit(V(36, (0, 1.5, 2), vel=96), V(39, (1, 3), vel=84), V(42, EIGHTHS, vel=56), fills=[FILLS["snare16"]], kit=24),
            ],
            lead=[
                P("melody", 98, 64, 88, vel=80, name="crystal", plan=["drive", "flow"], cells=["busy", "flowing"], echo=0.75),
                P("melody", 9, 72, 96, vel=76, name="glockenspiel", plan=["drive"], cells=["medium", "busy"]),
                P("melody", 73, 62, 86, vel=82, name="flute", plan=["flow", "drive"], cells=["flowing"]),
            ],
            danger=[
                (P("tremolo", 44, 60, 84, vel=64, name="tremolo_strings"),
                 P("ostinato", 45, 48, 72, vel=70, name="pizz_ostinato", rate=0.25),
                 P("hits", 14, 52, 76, vel=70, name="bells", bars="phrase", beats=(0, 2))),
            ],
        ),
    },
    fx={
        "pads": {"reverb": (0.85, 0.3)},
        "lead": {"reverb": (0.85, 0.28), "delay": (0.75, 0.3, 0.2)},
    },
)

_e = module_exports(LEVEL)
AREA, KEY, BARS, CUES, STEMS, FX = _e["AREA"], _e["KEY"], _e["BARS"], _e["CUES"], _e["STEMS"], _e["FX"]


def generate(seed, bpm=None, key=None, bars=None, cue=None, motif=None):
    return arrange(LEVEL, seed, bpm, key, bars, cue, motif)
