# soundtrack-maker

Generate loopable, layered game music on your own machine: no cloud services, no paid tools,
no AI models. Python code writes the music as MIDI from rules and a seed, FluidSynth plays
it with a free soundfont, and the result is mastered into Ogg files ready for a game.

Each **level** (a stage, area or scene of your game) has **cues**, one per game state:
`calm` (exploring, planning, menus), `action` (combat, chases, timers) and, where defined,
`boss`. Each cue comes out as:

- **5 stems**: `pads`, `bass`, `percussion`, `lead`, `danger`. Same length and tempo,
  so a game can fade layers in and out with the action.
- **1 preview**: the 5 stems mixed together, for listening and choosing.

Every file loops seamlessly on an exact bar boundary, and the same seed always produces the
same files, bit for bit.

> Ten example levels ship with the project (meadow, desert, tundra, volcano, void, swamp,
> reef, autumn, crystal caves, crimson keep), each with its own key, tempo and instruments.
> Use them, change them, or add your own (see [Adding a level](#adding-a-level)).

## Requirements

- Linux (tested on Ubuntu 24.04)
- Python 3.11 or newer, with `venv` (`sudo apt install python3-venv` on Debian/Ubuntu)
- FluidSynth: `sudo apt install fluidsynth`
- `curl`, `make`
- Disk: about **55 MB per cue per seed** (mostly the 24-bit WAV masters). 8 seeds of every
  level is about 9 GB. The Ogg files alone are about 3 MB per cue per seed.
- RAM: about 1 GB per parallel job. The worker count adapts to free memory automatically.

## Quick start

```bash
sudo apt install fluidsynth python3-venv     # system packages (once)
make setup                                   # venv, pinned packages, soundfont (once, ~20 s)

make list                                    # levels, keys, tempos, cues
make level LEVEL=meadow SEEDS=1-4            # generate 4 seeds of one level
make check LEVEL=meadow                      # technical checks
```

Then listen (see [Listening and choosing](#listening-and-choosing)) and export the
seeds you like:

```bash
make export PICK="meadow:3"                  # -> export/meadow/
```

## Commands

| Command | What it does |
|---|---|
| `make setup` | Checks Python and FluidSynth, creates `.venv`, installs pinned packages, downloads and verifies the soundfont. Safe to re-run. |
| `make list` | Shows every level with its key, loop length and cues (with tempo). |
| `make level LEVEL=volcano SEEDS=1-20` | Generates seeds for one level (or `LEVEL=volcano,void`). Add `CUES=action` for one cue only. |
| `make music SEEDS=1-8` | Generates seeds for every level. |
| `make check [LEVEL=...] [SEEDS=...]` | Validates built files (see [Checks](#checks)). Exits non-zero on failure. |
| `make check-full` | Checks plus a rebuild of one seed per cue to prove determinism. |
| `make export PICK="volcano:3 keep.boss:7" [OUT=path] [WAV=1]` | Copies chosen seeds into a clean folder with stable names (`WAV=1` adds the WAV masters). |
| `make test` | Unit tests. |
| `make clean` | Removes Python caches. Never touches `stems/` or `export/`. |

`SEEDS` takes ranges and lists: `1-8`, `3,7,12`, `1-4,9`. `JOBS=4` limits parallel workers.

The same tools are available directly, with more options:

```bash
.venv/bin/python -m render.make_stems --help     # --bpm, --key, --bars, --motif, --out, ...
.venv/bin/python -m checks.run --help
.venv/bin/python -m render.export --help
```

## Output

```
stems/<level>/
├── <cue>/seed<N>/
│   ├── <level>_<cue>_<stem>_seed<N>.ogg   5 stems, Ogg Vorbis, 48 kHz stereo   ← for the game
│   ├── <level>_<cue>_<stem>_seed<N>.wav   5 stems, 24-bit WAV masters          ← for re-encoding
│   ├── <level>_<cue>_<stem>_seed<N>.mid   5 stems as MIDI                      ← open in a DAW
│   └── build.json                         key, BPM, bars, chords, instruments, loudness, tool versions
├── previews/<level>_<cue>_mix_seed<N>.ogg  all 5 stems mixed                    ← for listening
└── report.json                            results of the last `make check`
```

`make export PICK="volcano:3"` produces stable names without seed numbers:

```
export/volcano/
├── volcano_calm_pads.ogg … volcano_calm_danger.ogg      stems
├── volcano_calm_mix.ogg                                 preview mix
├── volcano_action_*.ogg
└── selection.json      per cue: seed, bpm, bars, key, loop_seconds, loop_samples, stems
```

Pick seeds per cue with `LEVEL.CUE:SEED`, e.g. `PICK="volcano.calm:3 volcano.action:7"`.
Add `WAV=1` to copy the WAV masters too. Exporting again into the same folder overwrites those
files and merges `selection.json`.

**Loudness:** each cue's full mix (all 5 stems) is normalised to -16 LUFS with a -1 dBTP
ceiling. Every stem of a cue gets the same gain, so the stems still add up to the preview.
A single stem on its own is quieter than the mix, by design.

## Listening and choosing

The checks cannot judge music. Generate many seeds, listen, keep few.

```bash
# Loop one preview (q to stop)
ffplay -nodisp -loop 0 stems/volcano/previews/volcano_calm_mix_seed3.ogg

# Audition every seed of a cue, twice each (q skips to the next)
for f in stems/volcano/previews/volcano_calm_mix_seed*.ogg; do
  echo "$f"; ffplay -nodisp -autoexit -loop 2 "$f"
done
```

Looping matters: listen across the loop point. A seed's cues share a chord progression and
melodic idea, so audition them together.

## How it works

```
seed ──► level spec ──► arranger ──► 5 MIDI stems ──► FluidSynth ──► effects ──► mastering ──► Ogg + WAV + preview
         (generators/   (chords, voicing,             (rendered 3x,   (filters,    (mix to -16 LUFS,
          <level>.py)    Markov melody,                middle copy     reverb,      shared gain and
                         drum grooves)                 kept)           delay)       limiter)
```

- **Seeded and deterministic.** All randomness comes from `random.Random` instances derived
  from the seed with SHA-256. Each stem has its own stream, so changing one part never
  reshuffles another.
- **Variety between seeds.** A level offers 2 to 4 alternatives for each stem (instrument,
  accompaniment style, groove, phrasing) plus several chord progressions. The seed picks.
  The progression and a one-bar melodic idea are chosen per seed, not per cue, so a seed's
  cues belong together.
- **Seamless loops.** Each stem is rendered as three back-to-back copies of the loop and only
  the middle copy is kept. Note releases, reverb tails and modulation from the end of the
  loop therefore flow into its start exactly as they would during playback.
- **Diatonic.** Every pitched note is in the level's key or mode; the checks enforce it.

## Checks

`make check` validates everything that can be measured:

- MIDI: every stem has the same length (an exact number of bars), tempo and time signature;
  notes are in key, inside each instrument's range, and monophonic parts never overlap.
- Audio: sample-exact durations for WAV and Ogg; no silent or clipped stems; true peak
  at or below -1 dBTP; mix loudness within 1 LU of -16 LUFS; no click at the loop point.
- `make check-full` also rebuilds one seed per cue and compares: MIDI and WAV must be
  byte-identical, Ogg must decode identically.

These are technical checks only. They say nothing about whether a cue sounds good.

## Customising

### Override tempo, key or length

```bash
.venv/bin/python -m render.make_stems --area meadow --cues calm --bpm 96 --key "A ionian" --bars 8 --seeds 1-4
```

Tempo must give a whole number of samples per bar at 48 kHz *and* an exact MIDI tempo.
In 4/4 that means one of: **60, 64, 75, 80, 96, 100, 120, 125, 128, 150, 160** BPM.
`--bars` must be a multiple of 4 (and of the progression length).

### Use your own melody (motif)

Put a short theme (1 to 2 bars, ABC or MIDI) in `motifs/` and pass it in. The generator
transposes it to the level's key and builds the lead around it (statement, sequence,
inversion) instead of using a seed-generated idea:

```bash
.venv/bin/python -m render.make_stems --area meadow --motif motifs/my_theme.abc --seeds 1-8
```

See [`motifs/README.md`](motifs/README.md) for an ABC template. Files in `motifs/` are never
modified by the tools.

### Adding a level

1. Copy an existing level, e.g. `cp generators/meadow.py generators/lighthouse.py`.
2. Edit the `LevelSpec`: `area="lighthouse"`, the key, progressions, tempos and palette
   (format below).
3. Add `"lighthouse"` to `LEVELS` in `generators/__init__.py`.
4. `make test` (fuzzes 25 seeds of every level for range, key and overlap errors), then
   `make level LEVEL=lighthouse SEEDS=1-4` and listen.

Cues are not fixed: name them after your game's states (`menu`, `explore`, `stealth`,
`chase`...) and give each its own tempo and palette.

### Private, game-specific levels

To keep levels for your own game out of the shared repo, put the module in
`local/generators/` instead (the whole `local/` folder is git-ignored). It is picked up
automatically: `make list` marks it `[local]`, and `make level`, `make check` and
`make export` work with it as with the bundled levels. Write it exactly like a bundled level
(`from .common.arranger import ...` works there too).

A level spec, trimmed to one alternative per stem:

```python
LEVEL = LevelSpec(
    area="lighthouse",
    key="D mixolydian",                          # tonic + ionian/dorian/phrygian/lydian/mixolydian/aeolian/locrian
    progressions=[("I", "vii", "IV", "I"),       # one numeral per bar; case is ignored, chords are diatonic
                  ("I", "ii", "IV", "v")],       # the seed picks one
    bars=16,
    cues={
        "calm": CueSpec(                         # cue names are free-form; the first is the default
            bpm=96,
            pads=[P("arp", 46, 50, 84, vel=58, name="harp", shape=["up", "updown"])],    # list = alternatives
            bass=[P("roots", 32, 28, 55, vel=74, name="acoustic_bass")],
            percussion=[Kit(V(36, (0, 2), vel=64), V(70, EIGHTHS, vel=34), kit=8)],
            lead=[P("melody", 73, 62, 86, vel=70, name="flute", plan=["breath", "call"], cells=["sparse"])],
            danger=[(P("drone", 49, 36, 60, vel=42, name="low_strings"),                  # tuple = parts played together
                     P("hits", 47, 40, 55, vel=56, name="timpani", roll=True))],
        ),
        "action": CueSpec(bpm=120, ...),
    },
    fx={"pads": {"reverb": (0.8, 0.3)}},         # optional per-stem effect overrides
)
```

`P(writer, program, low, high, vel=..., volume=..., pan=..., name=..., **options)`:
`program` is the General MIDI program (0-127, 0-based), `low`/`high` the allowed MIDI note
range (keep it at least an octave wide). In options, a **list** means "the seed picks one";
a tuple is a literal value.

| Writer | Use | Options |
|---|---|---|
| `sustain` | held chords, voice-led | `size`, `split` (chance of mid-bar re-voicing), `swell` (CC11 cycle in beats) |
| `stabs` | short chords on a rhythm | `rhythms` (list of onset tuples), `length` |
| `arp` | broken chords | `shape` (up, down, updown, alberti, broken, pendulum), `rate`, `span`, `artic` |
| `pulse` | repeated chords | `rate`, `artic`, `accents` |
| `strum` | guitar-style strums | `rhythms`, `stagger` (ticks) |
| `sparkle` | sparse random glints | `density`, `rate`, `figure` (single, rise, fall, twinkle), `length` |
| `texture` | one held note with a slow swell (wind, sea) | `swell` |
| `roots` | bass: roots, fifths, approach notes | `patterns`, `artic` |
| `drive` | bass: driving eighths or sixteenths | `rate`, `patterns`, `artic` |
| `pedal` | bass: tonic pedal ostinato | `rhythm`, `length`, `octaves` |
| `walk` | bass: walking quarter notes | `artic` |
| `bass_sustain` | bass: whole-note roots | |
| `melody` | lead: motif plus Markov melody | `plan` (breath, drive, call, sparse, flow, answer), `cells` (long, sparse, medium, flowing, busy), `artic`, `echo` (beats) |
| `drone` | tonic and fifth per phrase | `swell` |
| `hits` | low hits on chord roots | `bars` (every, odd, phrase), `beats`, `length`, `roll` |
| `tremolo` | held root and fifth, high | `interval` |
| `ostinato` | repeating scale figure | `rate`, `shape` |

Drums: `Kit(V(note, pattern, pattern..., vel=, prob=, accent=, alt=), ..., fills=[...], crash=49, kit=0)`.
`note` is a General MIDI drum note (36 kick, 38 snare, 42 closed hat, 70 maracas, …), each
pattern a tuple of onsets in beats; the seed picks one pattern per voice. `kit` selects a
GeneralUser GS drum kit: 0 standard, 8 room, 16 power, 24 electronic, 25 808/909, 32 jazz,
40 brush, 48 orchestral. Shared rhythms and fills: `EIGHTHS`, `SIXTEENTHS`, `OFFBEATS`,
`QUARTERS`, `FILLS[...]` in `generators/common/arranger.py`.

Effects (`fx`) keys per stem: `highpass`, `lowpass` (Hz), `compressor` (threshold dB, ratio),
`chorus` (rate Hz, depth 0-1, mix), `delay` (beats, feedback, mix), `reverb` (room size, wet),
`gain_db`. Defaults are in `render/master.py`.

## Reproducibility and logging

The same seed, code and soundfont give identical files. Every build writes a `build.json`
next to its stems (parameters, instruments, loudness, tool versions, soundfont and generator
hashes) and appends one line to [`MANIFEST.md`](MANIFEST.md).

## Licences

- **This project's code**: MIT, see [`LICENSE`](LICENSE).
- **Music you generate**: yours. No machine-learning model or training data is involved: the
  notes come from the rules and random seeds in this code, the sounds from the soundfont below.
- **GeneralUser GS soundfont** (downloaded by `make setup`, not redistributed here) by
  S. Christian Collins: free for private and commercial music production. See
  `soundfonts/GeneralUser-GS-LICENSE.txt`.
- **FluidSynth** (LGPL-2.1) and **pedalboard** (GPL-3.0) are used as offline tools only; they
  are not part of the audio you ship.
- Full list of tools, versions and licences: [`MANIFEST.md`](MANIFEST.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `FluidSynth not found` during setup | `sudo apt install fluidsynth` |
| `Python venv support missing` | `sudo apt install python3-venv` |
| `Run 'make setup' first.` | The `.venv` is missing; run `make setup`. |
| `... does not give a whole number of samples per bar` | Use one of the valid tempos listed above. |
| A worker process is killed / the machine swaps | Use fewer workers: `make level LEVEL=... JOBS=4`. |
| `has not been built` from `make export` | Generate that seed first: `make level LEVEL=volcano SEEDS=3`. |
| A part is inaudible | Some soundfont presets are much quieter than others; swap the program in the level spec. `make check` flags stems that are fully silent. |

## Project layout

| Path | Contents |
|---|---|
| `generators/<level>.py` | one spec per level; `LEVELS` in `generators/__init__.py` lists them |
| `generators/common/arranger.py` | the data-driven arranger: part writers, drum grooves, phrase plans |
| `generators/common/` | bar grid, keys and chords, seeded RNG, Markov melody, motifs, MIDI writer |
| `render/` | `make_stems` (the pipeline CLI), FluidSynth rendering, loops, mastering, `export` |
| `checks/` | validation: MIDI, audio, determinism; `checks.run` is the CLI |
| `tests/` | unit tests and a 25-seed fuzz of every level |
| `motifs/` | your hand-written themes (never modified by the tools) |
| `scripts/setup.sh` | the setup script behind `make setup` |
| `local/` | your game-specific generators and notes, git-ignored |
| `stems/`, `export/`, `soundfonts/` | generated or downloaded, git-ignored |
| `MANIFEST.md` | log of tools, licences and every build |
