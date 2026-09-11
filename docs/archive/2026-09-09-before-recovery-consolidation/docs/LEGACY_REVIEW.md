# Review of the original prototype

The repository originally contained one 905-line, topic-specific script (`create_video.py`) and
one generated file (`atom_laser.mp4`). The video is 2:50 long, 1280×720, 15 fps, H.264, and has no
audio track.

The prototype proves that a science explanation can be decomposed into animated scenes, and its
content length is already within the desired range. It is not a viable daily system:

- scene functions encode one atom/laser story directly in Python rather than consuming a data
  contract;
- six manually named scene generators make every new topic a code change;
- speech bubbles and long intermediate text carry the explanation instead of narration;
- there is no source identity, second-pass review, Dutch path, TTS, captions, thumbnail, catalog,
  approval state, upload recovery, or release guard;
- 15 fps, 720p, and silent playback do not meet the new media contract;
- reusable drawing helpers are mixed with story-specific physics and the executable entry point,
  making visual changes risky and hard to test.

The new `src/erklaerbaer` package supersedes that design with a validated storyboard boundary,
eight reusable scene primitives, per-scene speech timing, deterministic category palettes,
versioned content identity, private-first YouTube state, and isolated external-service clients.
The original files remain untouched for comparison and provenance; no production module imports
them.

