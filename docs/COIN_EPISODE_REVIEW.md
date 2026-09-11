# German coin episode: honest review

Written 2026-09-10 from the finished build. Private upload https://youtu.be/M7vpfilsF1o,
episode `f2a5c884cc70a38e47bb1ac0`, cut `db971b7c297373777cc8b363`, 182.24 s, 3:03 on
YouTube. Sampled frames and measurements only. **I have not watched it end to end, and
technical validation is not creative acceptance.**

## Educational value

The script was already written and science-reviewed; I migrated it, not rewrote it, so the
words a child hears are the reviewed words. It is unusually careful for this age group:

- It says the dots stand for particles far too small to see, rather than implying they look
  like that. It says there is much free space between them, which the earlier evidence
  correction specifically asked for.
- It keeps the container rigid ("die Flasche bleibt ungefähr gleich groß"), so the pressure
  rise is honest rather than hand-waved.
- It frames pressure as a **difference** between inside and outside, not as an absolute, and
  the picture now shows both: fast teal particles inside, slower grey room air pressing down
  from above.
- It closes the loop honestly: air escapes through the gap, the difference falls, the coin
  drops. Nothing is claimed to be created or destroyed.

The one place the pictures work harder than the words is the recap, where the five steps now
appear on the sentence that says them rather than on a timer.

## Design, shot by shot

| Scene | Framing | What I checked | Verdict |
|---|---|---|---|
| 1 | establish | bear, jar, hands arriving, one clack | reads; hands arrive before the warmth, which is the causal order |
| 2 | micro | particles named before collisions are marked | good; the naming beat holds for 3.2 s |
| 3 | heat | warmth in the wall, then faster particles | direction of causation visible |
| 4 | pressure | inside against outside on one coin | the strongest shot; the comparison is the point |
| 5 | reaction | bear thinking, jar small | quiet, as a prediction beat should be |
| 6 | lift | gap opens, particles leave and do not return | reads at phone width |
| 7 | reset | coin falls back, hands still there | fine |
| 8 | recap | five steps arriving with the narration | fixed from a timer during review |

**The worst defect I found and fixed** was composition monotony: six consecutive scenes
originally used the same jar at the same size in the same place. That is the lesson the
guitar episode taught, at three times the scale. Each framing now has its own camera, and
every geometry is derived from it, so nothing drifted when the cameras moved.

Two other crossings were found by looking rather than by reasoning: the hands were drawn
inside the glass, and the room air scattered across the heading. Both are now impossible by
construction, and a test asserts that no shot reaches the heading.

## What is still weak

- The warm glow reads as a red pool at the base of the jar rather than heat in the wall.
- The grey downward ticks on the room air look like whiskers at full size.
- The escape hiss sits 35 dB under speech, outside the 20 to 25 dB band the other three
  anchors hit. It may be inaudible.
- The coin is a plain disc. It is the title object and deserves better art.
- The hand is one generated image mirrored, so both hands are the same hand.

## Speech, and what it cost to learn

The voice failed in a way worth recording. A 20-character line came back **spoken six times**
with long pauses between, because the narrator instruction never said to read the text once.
The bear instruction always had said so. Lines under 60 characters now carry that
instruction, which leaves the published Dutch episode untouched because it has no narrator
line that short.

That fix helped one short line and made another repeat, so synthesis for very short lines is
simply unreliable. Two deterministic post-processing steps now run on cached audio, cost
nothing, and are tested: internal silences longer than 0.6 s are collapsed, and for a short
line any reading that starts after the line is already due is dropped.

Measured after the fixes, every segment sits between 16.7 and 27.6 characters per voiced
second with no repeats.

## Spending

| Item | Reserved | Estimated actual |
|---|---:|---:|
| Gemini speech, 28 requests | $4.70 | $0.19 |
| BFL hand, 1 request | 20 credits | 6 credits |
| Science review, 3 calls | 3 of 24 | negligible |

The reservation model is **25 times** the estimate, which matches the owner's observed
0.0081 and 0.0334 CHF days. Nine of the 28 speech requests were waste: four recap takes
replaced by a different delivery, one cancelled in flight, and four short lines re-recorded.

`tts_characters` is now 28,934 of 30,000. **The next episode cannot run at all without
raising that**, which is a harder limit than the Gemini one.

## Lessons that generalise

1. Size a budget raise with a retry margin. Three of the four raises today existed only
   because the first was sized for a perfect run.
2. Check speech against its text before rendering. Characters per voiced second and the
   number of separated bursts catch a repeat in one pass, and rendering is the expensive step.
3. A sound anchor needs authored silence. Four anchors had nowhere to sit because the pauses
   were 0.2 s; the beats that carry a sound now get 0.5 to 0.75 s.
4. Reconcile a failed provider call by recording the outcome, then retry once deliberately.
   The code now records every failure so a retry is a reconciliation and not a guess.

## Second pass, 2026-09-11

Owner review found six things. Each was checked in the code or the frames before any change.

| Finding | Verified as | Resolution |
|---|---|---|
| Atoms outside the glass | 2.2% of particle centres, in the shoulders and base | paths now reflect off the drawn outline; zero, asserted per view |
| Not a bottle, coin too flat | chamfered octagon, flat ellipse | short-neck bottle and a thick struck lid, owner-chosen |
| Magnifier deforms | lens shape and rim change across the idle loop | rig defect on 2564932; needs Rive authoring |
| Hand shadow on the glass | `paste_prop` drew a drop shadow across the wall | shadow off for hands |
| Warm rim odd at the base | glow drawn along the floor | glow moved to the side walls the hands hold |
| Air leaves beside the lid | stream drawn outside the neck | stream starts inside the neck, under the lifted lid |

Two text simplifications were applied and the script re-reviewed. A third, the recap's
"im Durchschnitt", needs 336 characters against 307 remaining and is still open.

The halo pressure cue is the owner's choice, with one change: it scales with a particle's
speed and is labelled "jedes Teilchen drückt kräftiger". Tying it to space would have
contradicted the script's own line that the bottle stays the same size.
