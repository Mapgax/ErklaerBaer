# Owner setup and gates

> Current v3 implementation: [status and remaining gates](V3_IMPLEMENTATION_STATUS.md),
> [weekly feed/queue](WEEKLY_V3.md), [asset backup/recovery](ASSET_RECOVERY_V3.md).
> The Dutch guitar working render exists, but native rim repair and expressive narration are
> blocked. Legacy daily instructions below are historical and disabled; they are not an
> alternative production path. V3 creative acceptance has not been granted.


## Current v3 setup direction

Use [PRODUCTION_V3_PROMPT.md](PRODUCTION_V3_PROMPT.md) for current work. Rive Early Access and
the v2 exports are available; preserve backups and do not repeat historical installation gates.
A dedicated GET-only Nochmal feed, private selector, expressive TTS guards and local asset index
are implemented. Deployment, token setup, native repair and the expressive trial remain pending. No new subscription or public hosting is required. Feed deployment and
weekly automation activation remain separate authorized steps. Older daily-buffer setup below is
historical and superseded by the weekly target.

This guide separates autonomous implementation from required owner actions. For the current
six-action production upgrade, follow `SPEC.md` and `PRODUCTION_PROMPT.md`. Historical v1 editor
gates are complete; do not repeat per-still, screenshot, mesh or keyframe approvals. Never paste
credentials, OAuth codes, refresh tokens or `.env` contents into an issue or chat.

## Current upgrade — authorized work and the only owner gates

The owner is arranging one month of Cadet. The agent verifies access, uses official Rive MCP to
animate a duplicate of the approved master, exports the library and renders three full local
pilots. The target is six actions: Neutral, Lift, Explain, Think, Surprise and Aha.

Already authorized: local code/configuration changes, scoped MCP configuration where permissions
allow, Rive authoring writes, BFL artwork calls, Anthropic writing/review and Google narration
within the SPEC's persistent task caps. BFL: 300 additional reserved credits (USD 3), at most 15
requests; LLM: 24 additional calls; TTS: 30,000 additional characters. Respect remaining prepaid
funds/provider limits and monthly LLM/TTS caps. Preserve the original BFL ledger; implementing this
explicit new allowance may raise the old monthly ceiling but must never erase past usage. No top-up
or new subscription purchases. These caps are shared across retries/resumes, not renewed each run.

Ask the owner only when a specific missing account/credential/consent or enforced permission
action is unavoidable; when material scientific uncertainty or extra scope/budget cannot be
resolved; for consolidated creative sign-off on the completed action reel and all three pilots;
or before YouTube upload/publication/production activation. Continue unaffected work while waiting.
New assets may be used provisionally for local review; no production approval is inferred.

Use [official Rive MCP](https://rive.app/docs/editor/ai/mcp), documented at
`http://127.0.0.1:9791/mcp`, with the supported desktop/Early Access app and file open. Verify a
reversible edit and inspect it before relying on automation. Do not install a community MCP
replacement. Keep loopback access local; selected artwork/tool results may still enter the
connected coding model's context. Account actions are separate from recurring video production.

## Gate 1 — Environment

These are the original onboarding steps. Check each service's prerequisites independently before
its first live call. Missing YouTube/OAuth setup does not block authorized BFL, TTS or local rendering.
Keep default `DRY_RUN=true`; use scoped live invocations for authorized work.

1. Choose the Google account and YouTube channel that will own the videos.
2. Create a Google Cloud project and enable YouTube Data API v3 and Cloud Text-to-Speech.
3. Enable billing for Text-to-Speech. The repository budget is an additional guard, not a
   substitute for a Google Cloud budget alert.
4. Create a service account that can use Text-to-Speech and has no unrelated project roles.
   Download its JSON key to a private local path outside this repository.
5. Configure the OAuth consent application for production and create an OAuth *Desktop app*.
6. Create an Anthropic API key with a low provider-side spending limit.
7. Fill these owner-supplied `.env` values:

   - `ANTHROPIC_API_KEY`
   - `BFL_API_KEY` (local, bounded mascot-authoring passes only; see Gate 2)
   - `GOOGLE_CLOUD_PROJECT`
   - `GOOGLE_APPLICATION_CREDENTIALS` (absolute path to the service-account JSON)
   - `YOUTUBE_CLIENT_ID`
   - `YOUTUBE_CLIENT_SECRET`

8. Install the project and run `python3 -m erklaerbaer doctor --dry-run`.

The recurring jobs transmit only the six whitelisted public science fields to Anthropic, text
narration to Google Text-to-Speech, and finished media plus metadata to YouTube. The separate,
bounded mascot-design pass sends approved visual references and design prompts to BFL and artwork,
animation layers and scoped authoring commands/scripts to Rive. Science fact-pack excerpts may also
be sent to Anthropic. No materials, usage history, database state, child information, diagnoses,
credentials or unrelated repository content are sent to the visual services.

## Gate 2 — BFL concept art, Rive rig, and creative direction

This is an occasional authoring workflow. BFL and Rive are deliberately excluded from nightly and
daily production. Do not add their credentials to GitHub Actions.

### 2A. Create the isolated BFL project and prepaid limit

1. Open <https://dashboard.bfl.ai>, register, and verify the email address. BFL creates a default
   organization and project automatically.
2. In the organization sidebar, create a project named `ErklaerBaer Asset Design`. Use this
   dedicated project instead of an unrelated default project so its key and usage can be revoked
   independently.
3. At organization level, open **API -> Credits**, choose **Add Credits**, and buy USD 10 once.
   Leave automatic top-up disabled. Credits belong to the organization, so do not put unrelated
   BFL work in the same credit pool while this design gate is open.
4. In the `ErklaerBaer Asset Design` project, open its spending-limit controls. If the dashboard
   offers daily, weekly, and monthly limits, set them to USD 2, USD 5, and USD 10 respectively
   (200, 500, and 1,000 credits). The finite USD 10 prepaid balance and disabled auto top-up are
   the hard fallback if the limit controls are not visible for the account.
5. In that project, open **API -> Keys**, choose **Add Key**, and name it
   `ErklaerBaer local asset design`.
6. Copy the key immediately; BFL displays the complete value only once. Open the ignored local
   `.env` in an editor and set `BFL_API_KEY=bfl_...`. Do not paste the key into a terminal command,
   issue, commit, screenshot, or chat.
7. From the repository root, run `chmod 600 .env`, followed by
   `.venv/bin/python3 -m erklaerbaer doctor --dry-run`. This is a presence check only; it makes no
   BFL request and incurs no charge.

The original v1 implementation added a stricter local ceiling than the prepaid account balance: one concept per
command, 20 reserved credits per concept, and at most 100 reserved credits per calendar month. A
live CLI call uses the matching acknowledgement argument. For the authorized v2 pass, the agent
may supply that argument itself within the task allowance; it is not a per-image owner gate:

```bash
DRY_RUN=false .venv/bin/python3 -m erklaerbaer design-mascot \
  --pose neutral --confirm-max-credits 20
```

The reservation is deliberately conservative and is recorded before the network call. BFL's
reported charge is stored separately in the concept manifest. The command reuses an existing image
instead of overwriting or charging for it; a revised attempt needs `--revision 2` or higher.

The asset pass will use a fixed FLUX.2 endpoint and store its prompt, model, seed, source-image
checksums, and selected result locally. Generated text is forbidden. Anatomy-critical science
diagrams are not generated by BFL. Delete or revoke the BFL key after the approved mascot assets
have been exported and versioned.

### 2B. Create the private Rive authoring file

1. Open <https://rive.app/editor> and create or sign in to a Rive account.
2. The original v1 rig was authored on **Free**. The owner is now arranging one month of Cadet;
   verify the paid entitlement before export. Do not purchase or renew it on the owner's behalf.
3. In the personal workspace, create a private file named `ErklaerBaer Mascot Master`. Do not
   publish it to the Rive Community; Community files have different sharing and reuse behavior.
4. Create one portrait artboard, 1,200 x 1,600 px, with no background fill. The exact production
   video remains 1,920 x 1,080; the portrait artboard is only the reusable character asset.
5. Do not upload credentials, MINT records, narration or unpublished videos to Rive. Mascot artwork,
   animation layers and scoped animation scripts/commands belong in this file.
6. The initial neutral, lifting and explaining artwork and rig have already been approved.
   Continue on a duplicate; new Think/Surprise/Aha assets receive consolidated review after animation
   and local pilot assembly, not a blocking still-by-still gate.

Use `docs/RIVE_RIG.md` as the record of approved structure and `docs/PRODUCTION_PROMPT.md` for
continuation. All generated inputs must pass true-alpha and foreground-boundary checks before import.

The approved version-1 implementation is a hybrid rig: three flattened raster poses, a low-density
neutral mesh and head deformation, restrained whole-character idle motion, and manually aligned
vector blink overlays for every pose. Lift and Explain deliberately remain unmeshed; their gestures
come from the source images. There is no mouth or independent gaze animation. Additional head or
arm motion is justified only by a concrete scene and must not distract from the science content.

The paid plan enables export. Save `.rev` and `.riv` plus six-action 30 fps transparent clips;
preserve the v1 timelines `idle_loop`, `idle_loop 2` and `idle_loop 3` and record actual v2 names.
Prefer WebM only if decoded alpha and edge-compositing checks succeed; otherwise use PNG sequences.
Store versioned exports locally; Rive is not invoked for daily videos. MCP authoring and automated
export are separate capabilities: verify both and use the SPEC's bounded local bake fallback when
necessary. A missing connection blocks only dependent work.

### 2C. Review the combined creative direction

Prepare the six-action reel and three complete pilots: coin (de-DE), guitar (nl-NL), and animal
safari (nl-NL). Resolve technical issues and scientific corrections before requesting one
consolidated creative decision. Review:

- the original bear mascot and category palettes;
- actual causal mechanisms and factual evidence, timed to narration;
- small or absent mascot during explanations, with short purposeful reactions;
- the 105–120 words-per-minute pacing;
- the German and Netherlands-Dutch Chirp voices;
- pronunciation of scientific words and whether the adult voice feels calm rather than flat.

Do not proceed to YouTube upload until those choices are approved. Voice names and pacing remain
configuration values, so changing them does not require architecture changes.

Creative sign-off is not upload authorization. Prepare exact files/metadata before asking to upload.
Gates 3–5 below describe later deployment and are outside this local production task.

## Gate 3 — OAuth

Set `DRY_RUN=false`, then run:

```bash
python3 -m erklaerbaer setup-youtube
```

The command opens Google consent in the local browser, requests the single
`youtube.force-ssl` scope, displays the selected channel name and ID, and waits for the exact text
`YES`. It then finds or creates the language playlists. The refresh token, confirmed channel ID,
and playlist IDs are written directly to the ignored local `.env`; secrets are never printed.

Run `python3 -m erklaerbaer doctor --online` afterward.

## Gate 4 — Private YouTube pilots

Upload at least one German and one Dutch pilot. Watch the private videos in YouTube Studio, check
captions and thumbnails, and confirm the visible content marker has not leaked into the title.
Change each approved video from private to unlisted. That manual state change is the sole approval
signal; a private video can never be released by automation.

## Gate 5 — Production

Before public release:

1. Complete YouTube's API compliance audit and set `YOUTUBE_API_AUDIT_COMPLETE=true` only after
   confirmation.
2. Create the matching GitHub Actions secrets and variables listed below.
3. Build and approve a rolling 14-day buffer for the expected schedule.
4. Add the scoped dispatch token only to the private MINT-Bot repository.
5. Run both ErklaerBaer workflows manually in dry-run mode.
6. Enable the MINT-Bot dispatch and monitor the first two weeks.

## GitHub configuration

Create these **secrets** in ErklaerBaer:

- `ANTHROPIC_API_KEY`
- `GOOGLE_TTS_CREDENTIALS_JSON` (the complete TTS-only service-account JSON)
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`

Do **not** create GitHub secrets for `BFL_API_KEY` or Rive. They are local authoring tools, not
production dependencies.

Create these **variables** in ErklaerBaer:

- `GOOGLE_CLOUD_PROJECT`
- `YOUTUBE_CHANNEL_ID`
- `YOUTUBE_PLAYLIST_DE_ID`
- `YOUTUBE_PLAYLIST_NL_ID`
- `YOUTUBE_API_AUDIT_COMPLETE` (`false` until the audit succeeds)
- `PRODUCTION_ENABLED` (`false` through all gates; set to `true` only at Gate 5)

Create one secret in the private MINT-Bot repository:

- `ERKLAERBAER_DISPATCH_TOKEN`: a fine-grained token restricted to the ErklaerBaer repository and
  only the permission needed to create a repository dispatch. It grants no MINT-Bot access.

Create the MINT-Bot repository variable `ERKLAERBAER_ENABLED=false`. Change it to `true` only
after ErklaerBaer's `PRODUCTION_ENABLED` variable is also true and the dry-run dispatch succeeds.

GitHub-hosted runners receive credentials through their encrypted secret store, but the data
still leaves the local machine and is processed by GitHub. Logs must never enable shell tracing or
print environment variables.
