# Air and wave shots: measured faults and three options

Written 2026-09-10 from owner feedback on the reworked guitar review. Nothing here is rendered
into a video yet, and nothing here is creative acceptance. Stills only, no encode, no paid call.

Reproduce every picture with:

```bash
.venv/bin/python3 scripts/preview_wave_options.py
```

Output lands in `build/v3/wave-options/`.

## What is actually wrong

Each number is measured from the delivered geometry, not estimated. See `0-defects.jpg`.

| Fault | Measurement | Cause |
|---|---|---|
| Grey corridor does not meet the box | corridor top y=540, box front face top y=582.8 | `WINDOW` in `collage_guitar` was authored independently of the paste box |
| Corridor is drawn upwards, then right | pen starts 26 px below the top-left corner and hooks up | `air_window` opens each edge with a 26 px cap before the long run |
| Teal coupling bar leaves the box | bar reaches x=751.6, face ends at x=740 | the bar carries the air displacement while the box face stays still |
| Cardboard and strings are pixelated | close-up crops 615x190 authored pixels into a 1460x450 slot | the prop was drawn at 960x610 and enlarged 2.4x afterwards |
| Air arrives without being introduced | field grows in over 0.8 s under the heading "Elastiek en steunpunten" | the air is revealed on scene 3's second beat, before the word is spoken |

## Fixes common to all three options

- The prop is authored at the width it will occupy. `guitar()` and `guitar_layers()` now take a
  `scale`, so no drawn edge is ever enlarged. At `scale=1.0` the output is pixel-identical to the
  delivered frames, verified by differencing scene 4 at 1.9 s.
- The coupling cue becomes a bow of the face itself: its ends stay pinned to the box corners and
  only the middle moves, by exactly the displacement of the air column it touches. It cannot leave
  the box because it is the box.
- The air is introduced in two beats instead of one. It fades in **at rest** and is named
  (`luchtdeeltjes`), and only then does the box start pushing. A child sees that air is already
  there before anything travels through it.
- Box and ear are larger, so a particle is a bigger share of what a phone shows.

## The three options

`option-a.jpg`, `option-b.jpg`, `option-c.jpg` each show the same five beats.
`2-phone.jpg` shows all three at 420 px, the width that decides whether a mark reads.

**A, pen with corrected geometry.** Keeps the drawn corridor. It now starts exactly on the box
face, is exactly as tall as that face, and is drawn as one continuous stroke with no upward hook.
Cheapest change; keeps the existing pen vocabulary. It still frames the air, which sits awkwardly
against the claim that air is already everywhere.

**B, paper strip.** Replaces the drawn frame with a torn kraft strip that unrolls from behind the
box towards the ear. The air lives on an object in the collage rather than inside a diagram.
Tactile and consistent with the paper world; the strip does add a surface the physics does not have.

**C, open air, no frame.** No corridor at all. Five rows of particles fill the whole gap from the
box face to the ear. The box and the ear are the only anchors. Reads best at phone width, carries
the density banding furthest, and is the only option that does not contradict the "air is already
everywhere" rule.

## Recommendation

C, with A's corrected pen kept for the ear cutaway only, where a drawn line genuinely reveals
something hidden. B is the fallback if the open field feels too diagrammatic in motion.

## Intro

The 12-second intro exists and is built: `artifacts/review-v3/intro/fb10cd42eb4001c23272e5ef/`,
with a 6-second variant at `4f5e409cbafc224f0b946b96`. The uploaded Private video carries the
episode without it. `3-intro.jpg` shows the card. It holds one still image for its whole length,
which is the same defect as any unchanging stretch; the 6-second variant is the safer choice.
