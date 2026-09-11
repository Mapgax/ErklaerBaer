# ErklaerBaer Rive rig

> Current review, 2026-09-09: complete 175.03-second Gemini guitar episode `cedfada8807f70f3fe6b4a2c`, repaired native v3 bear, and a reusable 12-second original synthesized intro are rendered and checked. Combined 187.03-second cut: `artifacts/review-v3/intro/fb10cd42eb4001c23272e5ef/full-review.mp4`. YouTube file access is resolved; upload `https://youtu.be/z_1Fx6L3N_Q` is saved and verified Private in the channel content list, with Dutch captions. Native guitar prop Rive assets and consolidated owner acceptance remain open. Earlier checkpoints below are historical.

> Current v3 implementation: [status and remaining gates](V3_IMPLEMENTATION_STATUS.md),
> [weekly feed/queue](WEEKLY_V3.md), [asset backup/recovery](ASSET_RECOVERY_V3.md).
> The Dutch guitar working render exists, but native rim repair and expressive narration are
> blocked. Legacy daily instructions below are historical and disabled; they are not an
> alternative production path. V3 creative acceptance has not been granted.


## Approved v3 repair and reuse

V2 is technically exported but requires creative revision. Follow
[PRODUCTION_V3_PROMPT.md](PRODUCTION_V3_PROMPT.md): preserve the v1 master and v2 exports, duplicate
before v3 edits, trace the magnifying-glass rim defect through source/cleanup/mesh/bake, and use a
fixed visible-bounds crop/pivot. Extend Rive use to reusable layered props; retain deterministic
science motion and offline baking. Index editable sources and exports locally; no Voyager Libraries
upgrade is required. The rim contour/UV correction was applied on duplicate 2564932 on 2026-09-09 and the native
capture shows a continuous rim. Full embedded/native runtime saves remain blocked by the Rive
process filesystem access; use the native Export/Save dialog into `assets/mascot/rig/v3/native`.
The document-only recovery .rev is saved there. Fresh runtime baking/loop inspection and prop
animation remain pending; existing video frames still show the old defect.

## Current production v2 — 2026-09-08

The current machine-readable contract is `assets/mascot/rig/rig-contract.json`. The approved v1
master remains file `2558769`; all v2 work is in duplicate `2561970`, named
`ErklaerBaer_Mascot (1)`. The duplicate is authored, state-machine checked, natively exported, and
runtime checked. Its corrected `.riv` produced all six fixed-step clips, and the full embedded
`.rev` is preserved beside it. Only the consolidated owner creative review remains.

The production controller is `ViewModel1.action`, a number from 0 through 5:

| Value | Action | Timeline | Runtime behavior |
|---:|---|---|---|
| 0 | Neutral | `idle_loop` | restrained 4-second loop with synchronized blink |
| 1 | Lift | `lift_v2` | short action, then hold |
| 2 | Explain | `explain_v2` | small indicating movement, then hold |
| 3 | Think | `think_v2` | tilt, then attentive hold |
| 4 | Surprise | `surprise_v2` | 1.5-second reaction and settle |
| 5 | Aha | `aha_v2` | 1.8-second nod/raised-paw reaction and settle |

Rive state-machine simulation selected the correct state for every value. The inherited
unconditional Any State to Lift transition was repaired. The v1 `pose` and other legacy inputs are
retained in the file for historical compatibility but are not the v2 production API. The Neutral
Solo key begins at frame 0. The accepted head bind rotation remains
`-0.10641551025538434` degrees.

The first cloud runtime export was rejected after a real bake: Full optimization retained only
`idle_loop` because the artboard had no bound data context, even though the editor could simulate
conditions against `ViewModel1.action`. The duplicate now binds `ViewModel1` instance `Instance` to
the artboard. The rejected runtime and its hash are recorded in the contract; it must never be used
as the canonical v2 runtime. The corrected native runtime is 11,743,468 bytes with SHA-256
`0e291bb163dc8a9e713a4fd04fe306457f795af501dc4163e3809c71441e0c75`. The 11,523,132-byte full
embedded `.rev` has SHA-256
`6cac4e9f47f18e32d4f3abc564b7f992872c0ea71a81085c4ce17f743d375196`.

Think, Surprise, and Aha use new RGBA pose assets meshed and bound to the existing central skeleton.
Lift and Explain reuse accepted artwork. The Lift raster already contains a stone; this is a held
pose limitation. A scene may coordinate it with one separate reveal prop, but must never depict a
second stone being lifted.

Production uses a fixed 30 fps transparent PNG-sequence library baked locally from the `.riv` with
the isolated official Rive runtime. Neutral loops against the global video clock; all other actions
play once and clamp to their final frame. The renderer does not stretch clips to narration length.
The bake produced 419 frames. `mascot-qa.json` records mixed alpha, minimum alpha coverage above
26%, safe bounds, a 0.0027 mean-error Neutral loop seam, detectable one-shot motion, and distinct
non-Neutral action starts. The labelled six-action reel is
`artifacts/review-v2/six-action-reel.mp4`.

## Historical continuation note — 2026-09-07

The v1 three-pose editor rig is approved. The six-action extension and local pilots are authorized
in `SPEC.md` and `PRODUCTION_PROMPT.md`. Those instructions supersede the historical “stop and
send a screenshot” gates below. Do not repeat approvals or require owner operation of timelines.
Generate, animate, export and render provisional v2 assets autonomously, then request consolidated
review of the finished action reel and three local pilots.

Use the official desktop [Rive MCP integration](https://rive.app/docs/editor/ai/mcp), verifying its
actual capabilities. Work in a duplicate of the approved
[master](https://editor.rive.app/file/erklaerbaer_mascot/2558769), preserve bind poses and eyelids,
and save `.rev` authoring backups as well as `.riv` exports. Cadet entitlement was verified. This
paragraph is retained as historical context; Think, Surprise and Aha are implemented but remain
provisional and not owner-approved.

## Historical v1 authoring guide

This guide converts the three owner-approved BFL concepts into one reusable hybrid Rive rig. The
complex felt texture stays raster-based. Rive adds pose switching, subtle mesh deformation, face
controls, and reusable animation timelines. This preserves visual depth without creating thousands
of expensive vector paths.

The v1 authoring phase used **Free**. Its preview gate has passed; the owner is now arranging the
paid export phase. Runtime `.riv` export requires a paid plan.

## Contract

The machine-readable names and values are fixed in
`assets/mascot/rig/rig-contract.json`. These names are an API between Rive and the future GitHub
renderer, so capitalization and underscores matter.

- Artboard: `ErklaerBaer_Mascot`, 1200 x 1600, transparent, marked as a Component.
- Root group: `MascotRoot`.
- Pose Solo: `PoseSolo`.
- Pose children: `pose_neutral`, `pose_lift`, `pose_explain`.
- State machine in the current Rive file: `State Machine 1`.
- Inputs: `pose`, `talk`, `emphasis`, `look_x`, and `look_y`.

Only `pose` is visually wired in the current raster-based rig. `talk`, `emphasis`, `look_x`, and
`look_y` are reserved runtime inputs: wiring them requires separate mouth/pupil artwork that is not
present in the three source images. The unused editor input `Number 1` is not part of the contract
and has no effect.

The approved version-1 creative scope intentionally stops at pose selection, restrained idle/head
motion, and blinking. Mouth and independent gaze animation are out of scope. Lift and Explain stay
as unmeshed raster poses; their bones may look misaligned in Design mode but do not deform or render
over those images. Do not reposition the neutral skeleton to match them.

## Gate 2D — import and pose structure

Complete only this section first, then send a screenshot of the whole editor including the
Hierarchy and Assets panels.

1. Open the private file `ErklaerBaer Mascot Master` and remain in **Design** mode.
2. In the Hierarchy, double-click `Artboard`, rename it exactly `ErklaerBaer_Mascot`, and confirm
   that its size remains **W 1200 / H 1600**.
3. With the artboard selected, enable its **Component** toggle in the Inspector. Depending on the
   editor version this appears as the small component/cube action near the artboard name. The
   keyboard alternative is `Shift+N` with the artboard selected.
4. In the bottom-left **Assets** panel click `+`, choose the image/file import action, and select all
   three files below. In the macOS file picker, press `Cmd+Shift+G`, paste the containing directory,
   press Return, then select all three PNGs.

   ```text
   /Users/andreas/Projects/AI/ErklaerBaer/assets/mascot/rive-input/v1/pose-neutral-clean.png
   /Users/andreas/Projects/AI/ErklaerBaer/assets/mascot/rive-input/v1/pose-lift-clean-v2.png
   /Users/andreas/Projects/AI/ErklaerBaer/assets/mascot/rive-input/v1/pose-explain.png
   ```

5. Drag each imported asset from **Assets** onto the same artboard. They are three alternate states
   of one character, so place them exactly on top of each other, not next to each other. In the
   Inspector give every image the identical transform: **Position X 600 / Y 800**, **Scale X 100% /
   Y 100%**, **Origin X 50% / Y 50%**, and **Rotation 0°**. The 1024 x 1360 source canvas then fits
   inside the 1200 x 1600 artboard with a safe border.
6. Rename the three image nodes in the Hierarchy exactly:

   - `pose-neutral` becomes `pose_neutral`;
   - `pose-lift` becomes `pose_lift`;
   - `pose-explain` becomes `pose_explain`.

7. Select all three image nodes in the Hierarchy, right-click, and choose **Wrap in Solo**. Rename
   the resulting Solo `PoseSolo`. A Solo intentionally renders only one child at a time. Rive may
   move the shared **X 600 / Y 800** translation onto `PoseSolo` during wrapping and show the image
   children at local **X 0 / Y 0**. That is correct as long as `PoseSolo` itself is centered and all
   three children still share the same local transform.
8. Select `pose_neutral` using the Solo radio control. Then select `PoseSolo`, right-click, choose
   the group/wrap-in-group action, and name the outer group `MascotRoot`. On macOS, selecting
   `PoseSolo` and pressing **Cmd+G** is the reliable shortcut. Select the new group and press
   **Cmd+R** to rename it.
9. Confirm that the stage still shows the neutral bear on Rive's checkerboard transparency and that
   no pale rectangular background is visible.
10. Stop and send the requested screenshot. Do not add bones, meshes, animations, a state machine,
    or export settings yet.

## Gate 2E — basic idle motion

Create a reversible whole-character motion test before adding meshes or face controls. It verifies
the root transform, animation timing, and loop continuity without changing the approved artwork.

1. While still in **Design** mode, make `pose_neutral` active in `PoseSolo`. Do not switch Solo
   children while a timeline is active because Rive will automatically create an unwanted Solo key.
2. Switch to **Animate** mode and rename `Timeline 1` to `idle_loop`.
3. Set its playback type to **Loop**. Open the timeline-options selector using the small down arrow
   immediately after the time display (not the three-dot hierarchy-sort menu), choose **Duration**,
   and enter **00:04:00** (minutes:seconds:frames).
4. Select `MascotRoot`.
5. Key the following root transforms. Values at 0 and 4 seconds must match exactly so the loop has
   no visible jump:

   | Time | X | Y | Scale X | Scale Y | Rotation |
   |---:|---:|---:|---:|---:|---:|
   | 0.0 s | 600 | 800 | 100% | 100% | 0° |
   | 2.0 s | 600 | 796 | 100.3% | 100.7% | -0.3° |
   | 4.0 s | 600 | 800 | 100% | 100% | 0° |

6. Use gentle cubic interpolation and preview several complete loops. The result should read as
   breathing and a tiny weight shift—not bouncing, wobbling, or zooming.
7. Stop for visual approval before adding raster meshes. This test can be removed without changing
   the imported images or Solo hierarchy.

## Historical v1 animation and state machine

The current Rive file uses three four-second loop timelines because the editor retained duplicate
names: `idle_loop` for neutral, `idle_loop 2` for lift, and `idle_loop 3` for explain. All three keep
`FaceControls` at 100% Blend and reuse the accepted root/head motion. An explicit neutral Solo key
at the beginning of `idle_loop` ensures that the state machine can return from either alternate
pose.

`State Machine 1` contains `Neutral`, `Lift`, and `Explain` states. The numeric `pose` input routes
0 to Neutral, 1 to Lift, and 2 to Explain. All three routes, including return to 0, were exercised in
the editor preview on 2026-09-07. The synchronized blink was also inspected directly at 2:46 in
`idle_loop` and visibly closes both eyes.

The remaining speech, gaze, and emphasis inputs are intentionally unwired placeholders. Implementing
them needs separate raster or vector mouth and pupil layers; those cannot be derived reliably from
the flattened pose images without adding new artwork.

The lift and explain eyelids were manually aligned in their respective timelines and visually
accepted at the fully closed 2:43 frame on 2026-09-07. No extra mesh or bone deformation is required
for these two poses. Additional head or arm motion is a later scene-specific option, not part of the
base loop.

## Gate 2F — neutral raster mesh and central skeleton

1. In **Design** mode select `pose_neutral`, add **Deform → Mesh**, and use **Auto Trace** once with
   the default 50/50/50/50/0 settings.
2. Use **Generate** exactly once to add interior vertices. Do not repeatedly subdivide the mesh.
3. Accept the contour only if the limbs, ears, magnifying glass, and transparent gaps remain clean.
4. Finish mesh editing, select `MascotRoot`, activate the Bone tool with `B`, and create a single
   bottom-to-top chain using four click points: pelvis, belly centre, scarf knot, and forehead.
5. The three resulting bones are named `bone_root`, `bone_torso`, and `bone_head` from bottom to
   top. Do not add arm or prop bones at this gate.
6. Move the complete chain under `MascotRoot` and stop before binding so placement and parent
   direction can be reviewed independently.
7. Bind only the `pose_neutral` mesh to all three bones. With no individual vertices selected, set
   automatic weighting to **Blend 40% / Influences 2** and apply **Auto Weights** once.
8. Test the bind with only very small rotations before creating animation keys. Undo and correct
   weights if the magnifying glass, face, feet, or silhouette visibly shear.

## Gate 2G — face-control container

1. Keep the accepted `bone_head` idle keys at -0.106° / 2.0° / -0.106°.
2. In **Design** mode create an empty group at the scarf-knot/head-pivot position, name it
   `FaceControls`, and nest it directly under `MascotRoot` as a sibling of `PoseSolo` and
   `bone_root`.
3. Do not place it inside `PoseSolo`: Solo children are mutually exclusive and the blink overlay
   must render together with the active neutral raster.
4. Keep `FaceControls` above `PoseSolo` in the hierarchy so the vector overlays render over the
   active raster pose.
5. Preserve each bone's authored bind-pose rotation as the neutral animation value. A nearly zero
   value such as `-0.106°` is still meaningful and must not be rounded to zero after binding.
6. Do not use a Rotation Constraint from `FaceControls` to `bone_head`. The bone's world-space
   orientation includes the vertical bone axis and makes the overlays jump sideways.
7. Instead, key `FaceControls` rotation directly in `idle_loop`: 0° at 0 s, 2.106° at 2 s,
   and 0° at 4 s. This follows the head's relative change from -0.106° to 2.0°.

## Gate 2H — blink overlay

1. Keep the two blink groups under `FaceControls`: `blink_left` at -4° and `blink_right` at +3°.
2. Animate each group's **Blend** property in `idle_loop`; do not animate the raster eyes.
3. Use the synchronized 60 fps keys 0% at 0:00, 0% at 2:36, 100% at 2:40, 100% at 2:46,
   0% at 2:50, and 0% at 4:00.
4. The two equal 100% keys create a short fully closed hold; the four-frame ramps close and reopen
   the lids without leaving the brown overlays visible during the rest of the loop.

## Why Solo instead of one heavily deformed image

The lift and explain poses change the arm silhouette substantially. Rive's Solo is intended for
switching between alternate poses or rigs and is more reliable here than forcing a neutral raster
through extreme mesh deformation. The approach also prevents facial or anatomical distortion.

Official references: [Rive Solos](https://rive.app/docs/editor/manipulating-shapes/solos),
[raster meshes](https://rive.app/docs/editor/manipulating-shapes/meshes),
[bones](https://rive.app/docs/editor/manipulating-shapes/bones), and
[runtime export](https://rive.app/docs/editor/exporting/exporting-for-runtime).
