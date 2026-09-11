# Rive rig review

This is the historical v1 acceptance record. Intermediate pending gates were resolved by later
entries below. The v2 work is specified in `docs/SPEC.md` and `docs/PRODUCTION_PROMPT.md`; new
expressions/exports are not approved by this record. Do not repeat completed screenshot gates.
Record future owner acceptance separately against exact asset/build versions after presenting
the combined animation reel and pilot package.

## Gate 2D — structure

Passed on 2026-09-06 from owner-provided editor screenshots.

- Artboard: `ErklaerBaer_Mascot`
- Root: `MascotRoot`, X 600, Y 800, scale 100%
- Solo: `PoseSolo`
- Children: `pose_neutral`, `pose_lift`, `pose_explain`
- Transparent artboard with no pale source-image rectangle

## Gate 2E — basic idle motion

Technical review passed on 2026-09-06 from a 7.97-second, approximately 60 fps editor screen
recording. Two four-second cycles were visible. The root motion was restrained and the loop boundary
had no visible jump. This is accepted only as the base idle layer: the whole raster still moves as a
single object, so local mesh/face motion remains required before the creative animation gate.

## Gate 2F — neutral mesh

The neutral raster mesh contour and one `Generate` subdivision pass were visually accepted on
2026-09-06. The contour preserves the ears, limbs, magnifying glass, and transparent gaps. Interior
vertices cover the head, chest, abdomen, and legs without excessive subdivision. The central
three-bone chain was also visually positioned from pelvis through belly and scarf knot to forehead;
hierarchy direction, naming, and weights remain gated.

The hierarchy direction and bone placement were subsequently accepted: `bone_root` is the parent
of `bone_torso`, which is the parent of `bone_head`, and the complete chain is nested under
`MascotRoot`. The neutral mesh was then bound to all three bones and Auto Weights was applied once
with Blend 40% and a maximum of two influences per vertex. A deformation test remains gated.

The first animated head test (`bone_head` from -0.106° to 0.65°) was rejected as imperceptible. In
the 11.2-second, approximately 60 fps editor recording at 32.9% zoom, the detected head centroid
moved by less than one screen pixel. The next review value is 2.0°; the neutral endpoints remain at
-0.106°.

The 2.0° revision passed on a 10.47-second, 60 fps recording. At the enlarged review scale the head
centroid moved about 4.9 screen pixels while the face, scarf, magnifying glass, and lower body kept
their shapes. The local head motion and neutral-mesh weights are accepted for the base idle rig.

The `bone_head` deformation test passed at 2 degrees. Compared with its authored neutral rotation
of -0.106 degrees, the face, scarf, magnifying glass, feet, and lower body showed no material shear.
The authored -0.106-degree rotation is the bind-pose baseline and must not be normalized to zero.

## Gate 2G–2H — face controls and blink

Accepted in the Rive editor on 2026-09-07. `FaceControls` is a direct child of `MascotRoot`, above
`PoseSolo`, with `blink_left` and `blink_right` as children. A world-space Rotation Constraint was
rejected because the vertical orientation of `bone_head` rotated and displaced the overlays. The
constraint was removed.

`FaceControls` now follows the accepted head motion through explicit `idle_loop` rotation keys:
0 degrees at 0 seconds, 2.106 degrees at 2 seconds, and 0 degrees at 4 seconds. This reproduces the
head bone's 2.106-degree relative change without inheriting its bone-axis orientation.

Both blink groups use Blend keys at 60 fps: 0% at 0:00 and 2:36, 100% at 2:40 and 2:46, and 0% at
2:50 and 4:00. The normal state therefore shows the raster eyes, while the two vector overlays form
one short synchronized blink per four-second idle cycle.

## State-machine integration

Accepted in the Rive editor on 2026-09-07. The implemented state machine is currently named
`State Machine 1` and contains `Neutral`, `Lift`, and `Explain`. Input `pose` selects Neutral at 0,
Lift at 1, and Explain at 2. Each transition and the return from both alternate poses to Neutral were
verified in the running editor preview.

The associated timelines are `idle_loop`, `idle_loop 2`, and `idle_loop 3`. Rive retained the
duplicate-generated names for the lift and explain timelines. Each starts with its corresponding
`PoseSolo` selection; `idle_loop` includes an explicit `pose_neutral` key so returning to pose 0 is
deterministic. `FaceControls` Blend is 100% in all three timelines. The blink was visually verified
at the fully closed 2:46 key in `idle_loop`.

Inputs `talk`, `emphasis`, `look_x`, and `look_y` exist but are not visually wired because the
approved source poses are flattened raster images without separate mouth or pupil layers. The
additional editor input `Number 1` is unused and has no runtime role.

The owner manually realigned both eyelids for `idle_loop 2` and `idle_loop 3`. Direct inspection at
2:43 on 2026-09-07 confirmed that the fully closed overlays sit on the Lift and Explain eyes. The
three-pose blink implementation is accepted.

The production scope intentionally excludes mouth and independent gaze animation. Only the neutral
pose uses the skeleton/mesh for local head motion. Lift and Explain remain unmeshed because their
approved gestures are already clear; adding deformation would increase visual activity without an
explanatory benefit. Extra head or arm motion requires a scene-specific reason and separate review.

## Source-asset cleanup

Accepted on 2026-09-07:

- `pose-neutral-clean.png` removes only the trapped opaque background remnant between the bear and
  magnifying glass.
- `pose-lift-clean-v2.png` shortens the rear scarf tail while retaining a natural visible end. The
  first `pose-lift-clean.png` revision was rejected because it removed too much and left a stump.
- Both replacement assets remain 1024 x 1360 RGBA images. `pose-explain.png` is unchanged.
- Use asset replacement in Rive; do not delete and re-import the existing stage objects.
