"""MIDI checks: shared grid, key, ranges, monophony."""

from __future__ import annotations

from pathlib import Path

import mido

from .common import Result, load_build, stem_files


def _track_notes(track: mido.MidiTrack) -> list[tuple[int, int, int]]:
    """(start, end, pitch) for every note in a track."""
    now, open_notes, notes = 0, {}, []
    for msg in track:
        now += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            open_notes.setdefault(msg.note, []).append(now)
        elif msg.type in ("note_off", "note_on"):
            starts = open_notes.get(msg.note)
            if starts:
                notes.append((starts.pop(0), now, msg.note))
    return notes


def _track_length(track: mido.MidiTrack) -> int:
    return sum(msg.time for msg in track)


def check_seed(seed_dir: Path) -> list[Result]:
    meta = load_build(seed_dir)
    label = f"{meta['area']}/{meta['cue']}/seed{meta['seed']}"
    results: list[Result] = []
    expected_ticks = meta["bars"] * meta["beats_per_bar"] * meta["ppq"]
    expected_tempo = round(60_000_000 / meta["bpm"])
    key_pcs = set(meta["key_pitch_classes"])
    allowed_accidentals = set(meta.get("allowed_accidentals", []))

    for stem, path in stem_files(seed_dir, meta, "mid").items():
        target = f"{label} {stem}"
        if not path.exists():
            results.append(Result("midi exists", target, False, str(path)))
            continue
        mid = mido.MidiFile(path)
        lengths = {_track_length(t) for t in mid.tracks}
        tempos = [m.tempo for t in mid.tracks for m in t if m.type == "set_tempo"]
        sigs = [(m.numerator, m.denominator) for t in mid.tracks for m in t if m.type == "time_signature"]
        results.append(Result("length = bar grid", target, lengths == {expected_ticks},
                              f"tracks end at {sorted(lengths)} ticks, expected {expected_ticks}"))
        results.append(Result("tempo", target, tempos == [expected_tempo] and mid.ticks_per_beat == meta["ppq"],
                              f"{tempos} us/qn, ppq {mid.ticks_per_beat}"))
        results.append(Result("time signature", target, sigs == [(meta["beats_per_bar"], 4)], str(sigs)))

        specs = {p["name"]: p for p in meta["stems"][stem]}
        for track in mid.tracks[1:]:
            name = next((m.name for m in track if m.type == "track_name"), "?")
            spec = specs.get(name)
            if spec is None:
                results.append(Result("part spec", f"{target}:{name}", False, "track not described in build.json"))
                continue
            notes = _track_notes(track)
            ptarget = f"{target}:{name}"
            if not notes:
                results.append(Result("not empty", ptarget, False, "no notes"))
                continue
            if not spec["drums"]:
                bad = sorted({p for _, _, p in notes if p % 12 not in key_pcs and p % 12 not in allowed_accidentals})
                results.append(Result("in key", ptarget, not bad, f"out-of-key pitches {bad}" if bad else meta["key"]))
            lo, hi = min(p for _, _, p in notes), max(p for _, _, p in notes)
            results.append(Result("range", ptarget, spec["lo"] <= lo and hi <= spec["hi"],
                                  f"{lo}-{hi} within {spec['lo']}-{spec['hi']}"))
            if spec["monophonic"]:
                ordered = sorted(notes)
                overlaps = [(a, b) for a, b in zip(ordered, ordered[1:]) if b[0] < a[1]]
                results.append(Result("monophonic", ptarget, not overlaps,
                                      f"{len(overlaps)} overlaps" + (f", first at tick {overlaps[0][1][0]}" if overlaps else "")))
            hanging = [n for n in notes if n[1] > expected_ticks]
            results.append(Result("notes end in loop", ptarget, not hanging, f"{len(hanging)} past loop end"))
    return results
