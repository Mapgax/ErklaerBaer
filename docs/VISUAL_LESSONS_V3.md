# Visual and audio lessons from the guitar benchmark

Written 2026-09-09 from measurements of build `18805514b7a5d97a7de8b683`, compared against the
earlier `cedfada8807f70f3fe6b4a2c`. These rules carry forward to coin, safari and the weekly
template. Each one names the evidence behind it. None of them is owner creative acceptance.

## 1. A science mark must be about one percent of frame width

The delivered air lattice drew particles 8 px across on a 1920 px frame, which is 0.42% of frame
width. At the 400 px width a phone gives the video that is under two pixels, and the density
banding the whole scene depended on was invisible. The rebuilt field draws them 18 px across,
0.94% of frame width, and the pulse reads at phone size.

Apply to safari: the numerals 6, 8 and 14 next to the highlighted legs must clear the same bar
before anything else about that shot is judged.

## 2. Trade particle count for particle size, holding the physics ratio fixed

The old field was 5 rows of 21 particles at 28 px spacing with 11 px displacement. The new one is
3 rows of 13 at 44 px spacing with 17 px displacement. Displacement over spacing went from 0.393
to 0.386, so the claim about how far air moves is unchanged, while every mark more than doubled.

Fewer, larger, correctly proportioned beats many, small and technically exact.

Apply to coin: the bottle's gas particles have the same problem and the same fix. Keep the mean
free path honest by holding the ratio, not the count.

## 3. Give a travelling disturbance a second, coarser cue

Individual particles crowding together is a fine cue at full size and a poor one at thumbnail
size. A soft density cushion now rides each compression maximum, derived from the same phase term
rather than animated separately. Decoded from the MP4, the cushions move 54 to 70 px per 0.2 s
step against the 61.6 px the particle phase predicts, so the two cues cannot drift apart.

## 4. Introduce once, then stop

A pen draws the viewing corridor around the air in about 1.2 s, on the beat where the narration
first mentions the air, then lifts. Decoded frames show the stroke reaching x=747, 975, 1237 and
finally 1317 across four samples, with the particles growing in behind it. It happens once more in
the episode, to open the ear cutaway. Nothing keeps drawing under the explanation.

The pen never draws the air itself. Air is already everywhere, and a pen conjuring particles would
imply it arrives from somewhere. It draws the frame; the particles fade in inside it.

## 5. Anchor every element to its cause, on screen

A bar on the right face of the sound box now moves with the nearest column of air, so the coupling
is visible rather than asserted. In the ear shot the drawn membrane stays still until the pressure
change has travelled the drawn distance: measured x is 1303.6 and 1303.5 at 2.0 s and 2.4 s into
the scene, then swings between 1298.7 and 1308.6 after the front arrives at 2.56 s.

Apply to coin: heat and pressure cues currently float free of their sources. Same defect.

## 6. No two consecutive scenes share a composition

Scenes 4 and 5 previously ran the same code branch with the same box, ear and lattice geometry,
differing only by an 8 s clock offset. That held one picture for 52.1 s, the longest unchanging
stretch in the episode. They are now two shots: the corridor, then a push in on the ear with a
cutaway. For a child who loses the thread when nothing changes, this matters more than any single
graphic.

## 7. Sound is the phenomenon, or it is absent

Four events in 175.03 s: the band released, the box taking up the vibration, the pressure change
arriving, the vibration dying. Each is synthesized locally, sits in measured silence after the
last segment of a scene, and coincides with something the picture is doing.

Measured in the final mix, each event has an RMS between 0.009 and 0.016 against speech at 0.166,
roughly 20 to 25 dB down, with 0.57 s of silence to sit in and near-silence in the 0.25 s that
follows. No event overlaps a speech segment.

No chime, sparkle or whoosh, and no music bed. A sound that decorates is a distractor; a sound
that is the phenomenon is an anchor. The unused `SoundCue` helper in `audio.py` stays unused: it
fires at scene start and is tied to nothing visible.

## 8. Pick the school script by coverage and licence, not by looks

Child-facing words are set in Berner Basisschrift 1, vendored at
`assets/fonts/berner-basisschrift/` with its notice. Every candidate had the curved l; the
differences that mattered were elsewhere.

| Font | Blocking problem |
|---|---|
| Deutschschweizer Basisschrift | No eszett. Paid BKZ licence for products used outside Switzerland. |
| Grundschrift beta | No accented Latin vowels, which Dutch needs. Non-commercial licence only. |
| Grundschrift Bilderschrift | An illustration font. No full stop, comma or exclamation mark. |
| Berner Basisschrift 1 | None. Open Font Licence, complete coverage. |

Coverage was tested by rendering every character the project uses and comparing each against the
font's undefined glyph. Do that before judging a typeface on appearance.

These families carry one weight. On-screen words are set larger and given one pixel of pen weight,
which thickens the stroke without deforming the letter. They still read lighter than the previous
bold face, which is the accepted cost of the correct letterforms. The brand wordmark keeps its own
font deliberately.

## 9. What none of this establishes

Sampled frames are not a viewing, and measured levels are not listening. Technical validation has
never been creative acceptance in this project and is not here either.

## 10. Geometry is checked against the object, not against the frame

Measured on 2026-09-10 from the build the owner reviewed. Three faults survived every
technical check because each one was internally consistent and wrong only in relation to
something else on screen.

| Fault | Measurement |
|---|---|
| Drawn corridor above the box face | corridor top y=540, front face top y=582.8 |
| Coupling bar off the face it belongs to | bar reached x=751.6, face ends at x=740 |
| Close-up enlarged after it was drawn | 615x190 authored pixels shown at 1460x450 |

Every constant that positions one element against another is now derived from that other
element. `AIR_SOURCE` and the field bounds come from `AIR_BOX`, and `face_bow` reads the
paste box it is given. A hand-typed rectangle beside a hand-typed paste box will drift.

Apply to coin and safari before anything else about those shots is judged.

## 11. Author a prop at the size it is shown

`guitar()` and `guitar_layers()` take a `scale`, and `paste_guitar` derives it from the slot
the prop will occupy. Nothing is drawn small and enlarged afterwards. At `scale=1.0` the
output is pixel-identical to the previous build, verified by differencing a rendered frame.

Enlarging a drawn mark is not a rendering detail. It is the difference between a sound hole
with a clean ellipse and one with visible stair steps, at the size a child actually watches.

## 12. A wave that spreads is a wave that came from somewhere

The air is no longer a corridor of three rows. It is a field that fills the space around
the box and fades into the paper at its edges, and the crowding spreads outward as circles
centred on the middle of the box face, the way rings spread from a stone in water.

Direction is structural, not cosmetic. A point can only move along the line away from the
source, and only after the retarded front has reached it, so the disturbance can never
appear to travel back into the box. The test asserts exactly that.

The soft rings and the particle crowding are both derived from the same retarded phase, so
the coarse cue and the fine cue cannot drift apart.

## 13. Introduce the air under the heading that names it

The field used to appear during the scene titled "Elastiek en steunpunten", nine seconds
before the narration said the word. It now appears at the start of the scene titled
"Lucht trilt": still, named `Luchtdeeltjes`, with the box at rest. Only then does the face
push. The first thing that moves is the cause, not the effect.

That freed scene 3's second beat, which now pulls out to the whole box with its face
visibly bowing. No composition is held across two consecutive scenes.

## 14. Check a sequence at several phases, not at one frame

The eardrum crossed the rim of its own cutaway, and no single-frame check found it, because
the canal walls only stuck out at the left and the drum only bulged at particular phases of
its cycle. `scripts/qa_v3_sequences.py` now samples every beat of every scene at six
moments and lays the frames out, because a beat is where the composition changes.

Where the geometry can be reasoned about, reason about it instead of sampling. The cutaway
parts are derived from the rim: the walls end on the chord at the canal height less half
their own stroke, so they meet the rim, and the drum is pulled back by the largest bulge it
will ever have. A test walks the whole push range and asserts nothing crosses.

| Part | Furthest point from the centre | Rim |
|---|---:|---:|
| Canal walls | 95.0 px plus 2 px of stroke | 98 px |
| Eardrum at full bulge | 76.7 px plus 3 px of stroke | 98 px |

## 15. Show pitch as a comparison, because one rate alone shows nothing

Scene 5's second beat used to hold the ear close-up while the narration explained that a
faster vibration makes a higher tone. A single vibrating band cannot show that; there is
nothing to compare it against.

The beat is now two identical boxes, one at 1.8 times the shown frequency and one at 0.6.
The speed of sound is the same for both, so what differs on screen is the spacing of the
rings, not how fast they travel. That is the honest picture of pitch, and it is the reason
the frequency became a parameter rather than a constant in the drawing code.

## 16. Close with the card you opened with

The outro is the intro's card answered: the same cream oval, the same wordmark, the raised
paw where a wave would be, and "Tot ziens!" in place of the tagline. Four seconds, built by
the same script as the intro so the two can never drift apart, and closed by the opening
melody falling to its tonic.

The rig has six baked actions and none of them is a wave. `aha` raises an open paw at head
height, which reads as a goodbye and is honest about what the rig can do. Faking a wave by
sliding the whole bear would have looked exactly like what it was.
