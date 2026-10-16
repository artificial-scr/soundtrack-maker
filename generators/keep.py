"""Level 10, Crimson Keep: a gothic fortress, oppressive and climactic; the finale.

D Aeolian. Pipe organ, choir, harpsichord, low brass and timpani. Three cues: `calm`,
`action`, and `boss` (150 BPM) for a final boss fight.
"""

from .common.arranger import EIGHTHS, FILLS, SIXTEENTHS, CueSpec, Kit, LevelSpec, P, V, arrange, module_exports

LEVEL = LevelSpec(
    area="keep",
    key="D aeolian",
    progressions=[("i", "vi", "vii", "i"), ("i", "iv", "v", "i"), ("i", "vi", "iv", "v"), ("i", "i", "vi", "vii")],
    cues={
        "calm": CueSpec(
            bpm=80,
            pads=[
                P("sustain", 19, 48, 72, vel=50, volume=78, name="pipe_organ", split=0.25),
                P("sustain", 52, 50, 74, vel=56, name="choir", swell=16),
                (P("sustain", 49, 48, 72, vel=54, name="low_strings"),
                 P("arp", 6, 55, 84, vel=50, name="harpsichord", shape=["alberti", "broken"])),
            ],
            bass=[P("roots", 43, 28, 55, vel=68, name="double_bass"), P("bass_sustain", 58, 28, 52, vel=64, name="tuba")],
            percussion=[
                Kit(V(36, (0,), (0, 2.5), vel=70), V(41, (3,), (2, 3.5), vel=50, prob=0.7), kit=48),
                Kit(V(36, (0, 2), vel=66), V(38, (1, 3), vel=40, prob=0.6), kit=48),
            ],
            lead=[
                P("melody", 60, 52, 77, vel=66, name="horns", plan=["breath", "call"], cells=["sparse"]),
                P("melody", 42, 48, 74, vel=70, name="cello", plan=["breath", "answer"], cells=["sparse", "medium"]),
                P("melody", 69, 55, 79, vel=68, name="english_horn", plan=["breath"], cells=["sparse"]),
            ],
            danger=[
                (P("drone", 19, 36, 60, vel=42, volume=75, name="organ_drone", swell=16),
                 P("hits", 47, 40, 55, vel=58, name="timpani", bars="odd", roll=True)),
                P("tremolo", 44, 55, 79, vel=48, name="tremolo_strings"),
            ],
        ),
        "action": CueSpec(
            bpm=125,
            pads=[
                P("stabs", 61, 48, 72, vel=78, name="brass_stabs"),
                P("pulse", 48, 50, 74, vel=66, name="string_pulse", rate=0.25, artic=0.5, accents=(0, 1.5, 3)),
                (P("sustain", 52, 50, 74, vel=66, name="choir"),
                 P("arp", 6, 55, 84, vel=58, name="harpsichord_run", shape=["broken", "pendulum"], rate=0.25)),
            ],
            bass=[P("drive", 43, 28, 55, vel=84, name="double_bass", artic=0.6), P("drive", 38, 28, 55, vel=86, name="synth_bass")],
            percussion=[
                Kit(V(36, (0, 1.5, 2), (0, 0.75, 2, 2.5), vel=104), V(38, (1, 3), vel=96), V(42, EIGHTHS, vel=62),
                    fills=[FILLS["toms"], FILLS["snare16"]], crash=49, kit=48),
                Kit(V(36, (0, 1.5, 2, 3), vel=102), V(40, (1, 3), vel=94), V(51, EIGHTHS, vel=60),
                    fills=[FILLS["mixed"], FILLS["toms_low"]], crash=57, kit=16),
            ],
            lead=[
                P("melody", 61, 52, 79, vel=88, name="brass_lead", plan=["drive"], cells=["medium", "busy"]),
                P("melody", 40, 60, 86, vel=84, name="violin", plan=["drive", "flow"], cells=["busy", "flowing"]),
                P("melody", 19, 55, 81, vel=74, volume=80, name="organ_lead", plan=["drive", "answer"], cells=["medium"]),
            ],
            danger=[
                (P("tremolo", 44, 55, 79, vel=70, name="tremolo_strings"),
                 P("ostinato", 42, 36, 60, vel=78, name="cello_ostinato", rate=0.25),
                 P("hits", 47, 40, 55, vel=92, name="timpani", bars="every", beats=(0, 2), roll=True)),
            ],
        ),
        "boss": CueSpec(
            bpm=150,
            pads=[
                (P("sustain", 52, 50, 74, vel=74, name="choir"),
                 P("stabs", 55, 60, 84, vel=76, name="orchestra_hits", rhythms=[[(0, 0.75, 1.5), (0, 1.5, 3), (0,)]], length=0.5)),
                (P("sustain", 19, 48, 72, vel=60, volume=82, name="pipe_organ"),
                 P("pulse", 48, 50, 74, vel=70, name="string_pulse", rate=0.25, artic=0.5)),
            ],
            bass=[
                P("drive", 38, 28, 55, vel=92, name="synth_bass", rate=0.25, artic=0.6),
                P("pedal", 43, 28, 55, vel=90, name="double_bass_pedal", octaves=True, length=0.3),
            ],
            percussion=[
                Kit(V(36, (0, 0.75, 1.5, 2, 2.75, 3.5), EIGHTHS, vel=106), V(38, (1, 3), vel=102), V(42, SIXTEENTHS, vel=56, accent=14),
                    fills=[FILLS["snare16"], FILLS["toms"], FILLS["mixed"]], crash=49, kit=16),
                Kit(V(36, (0, 0.5, 1.5, 2, 2.5, 3.5), vel=106), V(38, (1, 3), vel=100), V(51, EIGHTHS, vel=62),
                    fills=[FILLS["toms"], FILLS["toms_low"]], crash=57, kit=48),
            ],
            lead=[
                P("melody", 61, 52, 79, vel=94, name="brass_lead", plan=["drive"], cells=["busy"]),
                P("melody", 48, 60, 86, vel=88, name="fast_strings", plan=["drive", "flow"], cells=["busy", "flowing"]),
            ],
            danger=[
                (P("tremolo", 44, 55, 79, vel=76, name="tremolo_strings"),
                 P("ostinato", 42, 36, 60, vel=84, name="cello_ostinato", rate=0.25),
                 P("hits", 116, 36, 55, vel=100, name="taiko", bars="every", beats=(0, 1.5, 2, 3), length=0.5, roll=True),
                 P("hits", 47, 40, 55, vel=94, name="timpani", bars="every", beats=(0, 2), roll=True)),
            ],
        ),
    },
    fx={"pads": {"reverb": (0.8, 0.28)}, "lead": {"reverb": (0.7, 0.22)}},
)

_e = module_exports(LEVEL)
AREA, KEY, BARS, CUES, STEMS, FX = _e["AREA"], _e["KEY"], _e["BARS"], _e["CUES"], _e["STEMS"], _e["FX"]


def generate(seed, bpm=None, key=None, bars=None, cue=None, motif=None):
    return arrange(LEVEL, seed, bpm, key, bars, cue, motif)
