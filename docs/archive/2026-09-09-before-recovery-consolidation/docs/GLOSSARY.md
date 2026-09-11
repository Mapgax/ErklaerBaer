# ErklaerBaer glossary

> Current v3 implementation: [status and remaining gates](V3_IMPLEMENTATION_STATUS.md),
> [weekly feed/queue](WEEKLY_V3.md), [asset backup/recovery](ASSET_RECOVERY_V3.md).
> The Dutch guitar working render exists, but native rim repair and expressive narration are
> blocked. Legacy daily instructions below are historical and disabled; they are not an
> alternative production path. V3 creative acceptance has not been granted.


## V3 terminology

- **Nochmal feed:** authenticated read-only list of favorite topic IDs; distinct from the public
  MINT schedule and from eligibility for repetition. It contains no family history.
- **Production slot:** one persisted weekly selection and language; retries reuse it.
- **Asset bundle:** versioned editable artwork, Rive sources/runtime, baked clips and provenance.
- **Creative acceptance:** owner assessment of actual visuals and listening quality, separate from
  codec, timing, alpha and other technical checks.

The [v3 plan](V3_REDESIGN_PLAN.md) supersedes references to daily production in older entries below.

## API

An application programming interface: a documented way for one program to ask
another service to do something. ErklaerBaer uses APIs for script generation,
speech generation, and YouTube publishing.

## API scope

A permission granted to an application. The YouTube OAuth token needs a scope
that allows uploads, captions, playlists, and visibility changes. Broader scopes
increase the damage possible if a token is stolen, so permissions should remain
as narrow as the workflow permits. **Owner action:** approve the requested
YouTube scope once during setup.

## BFL / FLUX

Black Forest Labs (BFL) provides the FLUX image-generation and image-editing API. ErklaerBaer
uses it only during a bounded, human-reviewed mascot concept pass, never for daily videos or
anatomy-critical scientific diagrams. **Owner action:** create a dedicated BFL project, buy only
the documented prepaid credit amount, disable auto top-up, and keep its project-scoped key only
in the local `.env`.

## Canonical source

The authoritative input. MINT-Bot's deployed experiment and schedule JSON files
are canonical for video discovery; ErklaerBaer does not maintain a competing
copy by hand.

## Compliance audit

YouTube's review of an API project's use of the YouTube Data API. New API
projects can upload private videos, but their API uploads remain restricted to
private viewing until the project passes the audit. **Owner action:** submit the
audit form after the private uploader is working.

## Content version

A particular video treatment of an experiment. It is identified by the source
hash and renderer/template version. Changing MINT science content creates a new
content version instead of silently replacing an existing video.

## Dry run

A safe execution mode that validates and reports intended work without calling
paid services or changing YouTube. `DRY_RUN=true` is the initial default.
**Owner action:** leave it enabled until the environment gate is complete.

## GitHub Action

A workflow that runs on GitHub's infrastructure after a schedule, manual
request, repository event, or cross-repository dispatch. ErklaerBaer uses Actions
for discovery, generation, private upload, and daily release. **Owner action:**
configure the documented GitHub secrets and variables before enabling production.

## Idempotency

The property that repeating an operation has the same final result as doing it
once. If an upload job is retried, it must find and reuse the first uploaded
video rather than create a duplicate.

## LUFS

Loudness Units relative to Full Scale, a measure of perceived audio loudness.
The target near -16 LUFS keeps narration clear and consistent without being
aggressive.

## Made for kids

YouTube's audience designation for child-directed content. It changes data
collection and disables features such as comments and some notifications.
ErklaerBaer sets this on every upload. **Owner action:** ensure the selected
channel's overall audience configuration is compatible with per-video settings.

## OAuth

A consent mechanism that lets ErklaerBaer act on the owner's YouTube channel
without storing the Google password. **Owner action:** complete the browser
consent step using the Google account that owns the intended channel.

## Ordinal day

The number of complete calendar days since 1970-01-01. Even ordinal days are
German and odd ordinal days are Dutch. Unlike day-of-month parity, this remains
strictly alternating at month boundaries.

## Private, unlisted, and public

- **Private:** only the channel owner and explicitly invited users can watch.
  ErklaerBaer uses this for drafts awaiting review.
- **Unlisted:** anyone with the URL can watch, but the video is not generally
  discoverable. Changing a private draft to unlisted is the owner's approval
  signal.
- **Public:** discoverable on YouTube. Automation may make an approved video
  public only on the correct MINT day.

**Owner action:** review private drafts and change only approved ones to
unlisted in YouTube Studio.

## Refresh token

A long-lived OAuth credential used to obtain short-lived access tokens while
the owner is offline. It grants meaningful channel access and must be protected
like a password. **Owner action:** generate it through `setup-youtube`, store it
in `.env` and GitHub Secrets, and revoke it if exposure is suspected.

## Rig

A character split into independently movable layers or bones: for example head, eyes, mouth,
arms, paws, scarf, and props. A rig lets one approved mascot perform many repeatable poses without
redrawing or regenerating the character for every video.

## Rive

A 2D design and animation editor used to build the approved bear rig and export reusable motion
assets. It is an authoring tool, not a daily cloud dependency. **Owner action:** create a private
personal file on the Free plan and buy an export-capable plan only after the three-pose creative
gate is approved. No Rive password or API key belongs in `.env`.

## Scene primitive

A reusable, known animation pattern such as particles, a flow, a comparison, or
a macro-to-micro zoom. The LLM may select a primitive by name but cannot invent
or execute rendering code.

## Source hash

A short SHA-256 fingerprint of the science fields used by the video. The same
experiment, language, and source hash reuse the same video. A changed hash
requires a new reviewed version.

## SRT

SubRip Subtitle format: a plain-text caption file containing numbered text
segments and timestamps. ErklaerBaer derives SRT timing directly from its scene
narration rather than transcribing the finished audio.

## Storyboard

The validated data contract between script generation and rendering. It
contains scene order, narration, short labels, visual primitive choices, factual
anchors, and YouTube metadata.

## TTS

Text-to-speech: conversion of written narration into audio. ErklaerBaer uses
Google Cloud Chirp 3 HD. **Owner action:** create a Google Cloud project, enable
Text-to-Speech and billing, and provide a narrowly permitted credential.
