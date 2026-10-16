"""Level 5, Void: cosmic, weightless and eerie; very spacey.

B-flat Lydian (the raised fourth floats). 64 BPM when calm: halo and space-voice pads,
Star Theme and Echo Drops with delay. The action cue is a neon lane: sixteenth-note synth arps,
808/electronic kits and pulsing polysynth.
"""

from .common.arranger import EIGHTHS, FILLS, OFFBEATS, SIXTEENTHS, CueSpec, Kit, LevelSpec, P, V, arrange, module_exports

LEVEL = LevelSpec(
    area="void",
    key="Bb lydian",
    progressions=[("I", "ii", "I", "ii"), ("I", "vii", "iii", "ii"), ("I", "iii", "ii", "I"), ("vi", "ii", "I", "I")],
    cues={
        "calm": CueSpec(
            bpm=64,
            pads=[
                P("sustain", 94, 55, 79, vel=56, name="halo_pad", swell=[16, 32]),
                P("sustain", 91, 55, 79, vel=54, name="space_voice", swell=16),
                (P("sustain", 88, 55, 79, vel=52, name="fantasia"),
                 P("sparkle", 103, 72, 96, vel=50, name="star_glints", density=0.08, figure=["twinkle", "single"], length=1.0)),
            ],
            bass=[
                P("bass_sustain", 39, 28, 55, vel=62, name="synth_bass_2"),
                P("roots", 39, 28, 55, vel=60, name="synth_bass_2", patterns=(((0, "R", 4),), ((0, "R", 3), (3, "5", 1)))),
            ],
            percussion=[
                Kit(V(36, (0,), vel=60), V(42, (1.5, 3.5), vel=34, prob=0.7), kit=25),
                Kit(V(81, (0,), vel=30, prob=0.6), V(53, (2,), vel=26, prob=0.5), kit=24),
            ],
            lead=[
                P("melody", 103, 60, 88, vel=62, name="star_theme", plan=["sparse"], cells=["long", "sparse"], echo=1.5),
                P("melody", 85, 60, 84, vel=60, name="solo_vox", plan=["sparse", "breath"], cells=["long"]),
                P("melody", 102, 64, 88, vel=62, name="echo_drops", plan=["sparse", "call"], cells=["sparse"]),
            ],
            danger=[
                P("texture", 99, 40, 64, vel=50, name="atmosphere", swell=32),
                P("drone", 95, 36, 60, vel=44, name="sweep_drone", swell=16),
            ],
        ),
        "action": CueSpec(
            bpm=96,
            pads=[
                P("arp", 80, 55, 84, vel=56, volume=80, name="neon_arp", shape=["up", "pendulum", "updown"], rate=0.25, span=[5, 6], artic=0.5),
                P("pulse", 90, 55, 79, vel=58, name="polysynth_pulse", artic=0.4),
                (P("sustain", 94, 55, 79, vel=56, name="halo"),
                 P("arp", 98, 64, 90, vel=54, name="crystal_arp", shape="up", rate=0.25, span=6)),
            ],
            bass=[
                P("drive", 38, 28, 55, vel=84, name="synth_bass", artic=0.5),
                P("pedal", 39, 28, 55, vel=82, name="synth_bass_2", octaves=True, length=0.35),
            ],
            percussion=[
                Kit(V(36, (0, 2), (0, 1.5, 2), vel=100), V(39, (1, 3), vel=84), V(42, OFFBEATS, EIGHTHS, vel=60),
                    fills=[FILLS["half"], FILLS["snare16"]], kit=25),
                Kit(V(36, (0, 1.5, 2.75), vel=100), V(38, (1, 3), vel=90), V(42, SIXTEENTHS, vel=44, accent=14),
                    fills=[FILLS["toms"]], kit=24),
            ],
            lead=[
                P("melody", 81, 60, 86, vel=80, volume=80, name="saw_lead", plan=["drive", "flow"], cells=["busy", "flowing"], echo=0.75),
                P("melody", 103, 60, 88, vel=82, name="star_theme", plan=["flow"], cells=["flowing"], echo=0.75),
                P("melody", 87, 55, 81, vel=80, name="bass_and_lead", plan=["drive"], cells=["busy"]),
            ],
            danger=[
                (P("texture", 99, 40, 64, vel=66, name="atmosphere", swell=8),
                 P("ostinato", 90, 48, 72, vel=66, name="poly_ostinato", rate=0.25),
                 P("tremolo", 92, 60, 84, vel=60, name="bowed_glass")),
            ],
        ),
    },
    fx={
        "pads": {"chorus": (0.4, 0.3, 0.4), "reverb": (0.9, 0.32)},
        "lead": {"delay": (0.75, 0.35, 0.25), "reverb": (0.85, 0.28)},
        "danger": {"reverb": (0.9, 0.3)},
    },
)

_e = module_exports(LEVEL)
AREA, KEY, BARS, CUES, STEMS, FX = _e["AREA"], _e["KEY"], _e["BARS"], _e["CUES"], _e["STEMS"], _e["FX"]


def generate(seed, bpm=None, key=None, bars=None, cue=None, motif=None):
    return arrange(LEVEL, seed, bpm, key, bars, cue, motif)
