"""Level 4, Volcano: heavy, ominous and hot; a slow breathing glow over a nervous flicker.

C Phrygian, low register. The loop is 12 bars so the pads can "breathe" on a 6-beat cycle,
which at 80 BPM is 4.5 s, the lava's pulse. Sixteenth-note pizzicato and ember sparkles are
the flicker; taiko and low brass carry the weight.
"""

from .common.arranger import EIGHTHS, FILLS, CueSpec, Kit, LevelSpec, P, V, arrange, module_exports

BREATH = 6  # beats: 4.5 s at 80 BPM

LEVEL = LevelSpec(
    area="volcano",
    key="C phrygian",
    bars=12,
    progressions=[("i", "ii", "i", "i"), ("i", "vi", "vii", "i"), ("i", "ii", "vii", "i"), ("i", "i", "vi", "ii")],
    cues={
        "calm": CueSpec(
            bpm=80,
            pads=[
                P("sustain", 52, 48, 72, vel=60, name="choir", swell=BREATH),
                P("sustain", 49, 43, 67, vel=62, name="low_strings", swell=BREATH),
                (P("sustain", 19, 48, 72, vel=48, volume=80, name="organ", swell=BREATH),
                 P("sparkle", 102, 72, 96, vel=46, name="ember_flicker", density=0.15, rate=0.25, length=0.25)),
            ],
            bass=[
                P("pedal", 58, 28, 55, vel=74, name="tuba_pedal", rhythm=[(0, 2), (0, 1.5, 2, 3.5)], length=1.2),
                P("bass_sustain", 43, 28, 55, vel=70, name="double_bass"),
            ],
            percussion=[
                Kit(V(36, (0,), (0, 2.5), vel=78), V(41, (2, 3.5), vel=52, prob=0.8), kit=48),
                Kit(V(36, (0, 1.5), vel=80), V(45, (3,), vel=56), V(69, (0.5, 1.5, 2.5, 3.5), vel=30), kit=16),
            ],
            lead=[
                P("melody", 57, 48, 74, vel=70, name="trombone", plan=["breath", "sparse"], cells=["long", "sparse"]),
                P("melody", 60, 50, 77, vel=68, name="horns", plan=["breath", "call"], cells=["sparse"]),
                P("melody", 70, 46, 72, vel=74, name="bassoon", plan=["call", "sparse"], cells=["sparse", "medium"]),
            ],
            danger=[
                (P("hits", 116, 36, 55, vel=66, name="taiko", bars="odd", roll=True),
                 P("drone", 49, 36, 60, vel=44, name="low_drone", swell=BREATH)),
                P("ostinato", 45, 48, 72, vel=50, name="nervous_pizz", rate=0.25),
            ],
        ),
        "action": CueSpec(
            bpm=120,
            pads=[
                P("stabs", 61, 48, 72, vel=80, name="brass_stabs", rhythms=[[(0, 0.75, 1.5, 3), (0, 1.5, 3), (0, 0.5, 2, 2.5)]]),
                P("pulse", 48, 48, 72, vel=66, name="string_pulse", rate=0.25, artic=0.5, accents=(0, 1.5, 3)),
                (P("sustain", 52, 48, 72, vel=66, name="choir", swell=BREATH),
                 P("stabs", 55, 60, 84, vel=70, name="orch_hits", rhythms=[[(0,), (0, 1.5)]], length=0.5)),
            ],
            bass=[
                P("drive", 38, 28, 55, vel=88, name="synth_bass", rate=0.25, artic=0.6),
                P("pedal", 33, 28, 55, vel=90, name="finger_bass_pedal", octaves=True),
            ],
            percussion=[
                Kit(V(36, (0, 0.75, 2, 2.5), (0, 1.5, 2, 3.5), vel=104), V(38, (1, 3), vel=100), V(42, EIGHTHS, vel=64),
                    fills=[FILLS["toms"], FILLS["toms_low"], FILLS["snare16"]], crash=49, kit=16),
                Kit(V(36, (0, 1.5, 2, 3), vel=104), V(40, (1, 3), vel=96), V(51, EIGHTHS, vel=60),
                    fills=[FILLS["mixed"]], crash=57),
            ],
            lead=[
                P("melody", 61, 52, 79, vel=88, name="brass_lead", plan=["drive"], cells=["medium", "busy"]),
                P("melody", 30, 52, 79, vel=80, volume=80, name="distortion_guitar", plan=["drive", "flow"], cells=["busy"]),
                P("melody", 81, 55, 81, vel=86, name="saw_lead", plan=["drive"], cells=["busy"]),
            ],
            danger=[
                (P("hits", 116, 36, 55, vel=96, name="taiko", bars="every", beats=(0, 0.75, 2), length=0.5, roll=True),
                 P("tremolo", 44, 55, 79, vel=72, name="tremolo_strings"),
                 P("ostinato", 42, 36, 60, vel=78, name="cello_ostinato", rate=0.25)),
            ],
        ),
    },
    fx={"pads": {"reverb": (0.7, 0.25)}},
)

_e = module_exports(LEVEL)
AREA, KEY, BARS, CUES, STEMS, FX = _e["AREA"], _e["KEY"], _e["BARS"], _e["CUES"], _e["STEMS"], _e["FX"]


def generate(seed, bpm=None, key=None, bars=None, cue=None, motif=None):
    return arrange(LEVEL, seed, bpm, key, bars, cue, motif)
