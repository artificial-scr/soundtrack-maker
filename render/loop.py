"""Loop construction.

Rendered MIDI uses `circular_middle`: the loop is played three times back to back and the
middle copy is kept, so release tails and effect state wrap around the loop point exactly.

Audio that cannot be re-rendered (e.g. audio-model output) uses `crossfade_loop`: cut on an
exact bar multiple and fold the tail into the head with an equal-power crossfade.
"""

from __future__ import annotations

import numpy as np

REPEATS = 3


def circular_middle(audio: np.ndarray, loop_frames: int) -> np.ndarray:
    if len(audio) < REPEATS * loop_frames:
        raise ValueError("audio is shorter than the repeated loop")
    return audio[loop_frames : 2 * loop_frames].copy()


def crossfade_loop(audio: np.ndarray, loop_frames: int, sample_rate: int, fade_ms: float = 100.0) -> np.ndarray:
    """Cut `audio` to `loop_frames` and fold what follows into the head.

    The material after the cut fades out while the head fades in (equal power, 50 to 200 ms),
    so the end of the loop flows into its start without a click.
    """
    if not 50 <= fade_ms <= 200:
        raise ValueError("fade_ms must be between 50 and 200")
    n = int(round(sample_rate * fade_ms / 1000))
    if len(audio) < loop_frames + n:
        raise ValueError("need at least fade length of audio after the loop end")
    out = audio[:loop_frames].copy()
    t = (np.arange(n) + 0.5) / n
    fade_in = np.sin(t * np.pi / 2)[:, None]
    fade_out = np.cos(t * np.pi / 2)[:, None]
    out[:n] = out[:n] * fade_in + audio[loop_frames : loop_frames + n] * fade_out
    return out
