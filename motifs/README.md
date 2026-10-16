# motifs/

Human-written themes. **Source of truth: generators never overwrite these files.**

Add 2 to 3 short motifs (1 to 2 bars each) as ABC or MIDI. Use them with:

    .venv/bin/python -m render.make_stems --area meadow --motif motifs/meadow_main.abc --seeds 1-20

The motif is transposed to the area's key and snapped to its scale, then stated, sequenced
and inverted by the generator, which fills the rest of each phrase around it.

ABC template (D Dorian, 4/4, eighth-note unit):

```
X:1
T:meadow main motif (replace with your own)
M:4/4
L:1/8
K:Ddor
A2 G F E2 D2 | F2 A2 d4 |]
```
