# Production cadence

> Owner decision, 2026-09-13. Supersedes the weekly alternation of 2026-09-11 and the daily
> design below, which was never active and whose workflows have been deleted.

**Two videos a week.** German on Monday, Dutch on Thursday, each at 07:00 Europe/Zurich, each
on a topic never produced in any language. The slots are `[production_v3]` in
`config/settings.toml`. Two local scheduled tasks, `erklaerbaer-monday-german` and
`erklaerbaer-thursday-dutch`, run [the episode runbook](EPISODE_RUNBOOK.md). They need the Claude
app open on this Mac, because the speech cache, credentials and bear frames are local.

**Topic selection.** `scripts/next_topic.py` lists unused topics in an order fixed by the slot
date. A topic is used once any storyboard for it exists under `storyboards/`, so the tracked
tree is the record and nothing can be produced twice.

**Budget.** Speech and science review are bounded per calendar month: 360 Gemini requests,
750,000 characters and 200 LLM calls. That is ten episodes with retry margin, recorded as an
owner authorization in the ledger on 2026-09-13.

**Topic source.** The public MINT library at `https://mint-bot-nine.vercel.app/data/experiments.json`
is live and holds 60 topics in four categories: kuechenchemie, natur-tiere, technik and
weltraum-physik. Five have been touched by 2026-09-13, so 55 have never been used.

The "waiting to be redone" list the owner wants preferred is **not available**:
`https://mint-bot-nine.vercel.app/api/production-favorites` returns 404. The endpoint was
written into MINT-Bot but never deployed, and no `ERKLAERBAER_READ_TOKEN` was ever generated.
Until it is deployed, pick from the not-yet-done list.

**What gates a week is the drawing template, not the topic.** A topic whose mechanism already
has one is a short week. `vibrating-string` has `guitar-collage` and `gas-pressure` has
`coin-collage`. Any other mechanism needs a new template first, which is roughly a day.

**Rive is not needed for an episode.** Episodes use the baked frame library. Rive is only
needed when the bear himself changes, which has happened twice. When that is the case the
owner is told, because the export must go through the editor's own menu.

**A scheduled run builds and stops.** It writes the episode, reviews its own frames and speech
against the lessons in CLAUDE.md, fixes what it finds, uploads Private, records the result in
`docs/AGENT_STATUS.md`, and stops. Publishing and creative acceptance stay with the owner.

**The build catalogue is stale.** `catalog/videos.json` still lists the three v1/v2 pilots.
The two published v3 episodes were built by the direct scripts and are recorded under
`artifacts/review-v3/` instead. Reconciling the catalogue is open work.

---

# Private weekly queue and Nochmal feed

> For current delivery, subsequent owner authorizations, archives and remaining work, see [Recovery and next steps](RECOVERY_AND_NEXT_STEPS.md). The original requirements/history below remain preserved.

The local selector and read-only endpoint are implemented and tested with synthetic data.
**No live favorite data was fetched. No endpoint was deployed. No weekly automation is active.**
Guitar creative acceptance must precede coin/safari correction and wider production.

## Feed contract

MINT-Bot now contains `api/production-favorites.js`. It executes one read-only SELECT over
`mint.themen`, selecting rows whose derived `status = 'nochmal'` and `nochmal_tauglich = TRUE`.
This follows the actual Nochmal semantics and retains all qualifying IDs without the search
endpoint's 40-result limit. It does not read `mint.tage` or change schedules/experiments.

GET `/api/production-favorites` requires `X-Erklaerbaer-Read-Token`, backed by a separate
`ERKLAERBAER_READ_TOKEN` environment value of at least 32 characters. The feed refuses configuration
where this equals `MINT_WRITE_TOKEN`. The existing `checkMintRequest` now explicitly rejects the
read credential, even under a mistaken equal-token configuration. Do not distribute the write
credential to ErklaerBaer. No credential was generated or installed during this implementation.

Response fields are exclusively `schema_version: 1`, sorted unique `topic_ids`, and `revision`.
Revision is SHA-256 of the compact UTF-8 JSON ID array. It is stable while eligible membership is
unchanged; it intentionally contains no database revision, observation timestamps, family history,
child fields or unrelated state. All responses prohibit caching. Errors contain no raw DB details.
The endpoint still uses the existing MINT database connection implementation, which disables TLS
certificate verification. That inherited limitation needs a separate CA/configuration correction
before relying on the feed in production; no new database credentials or access were introduced.

The client sends the dedicated header only to the configured HTTPS feed. Redirects and URL query
credentials are rejected. It limits payload size, validates the exact schema/hash and stores an
independent local fetch time. Missing, malformed or more-than-24-hour-old snapshots block selection.
Unknown topic IDs are reported as errors. Fetching the feed is a third-party network call; no feed,
queue, favorites or family data is ever part of a BFL/TTS design request or public deliverable.

## Queue semantics

`private/production/queue.json` is gitignored and written with mode 0600 in a private directory.
A local advisory lock and atomic replace cover selection, claim and completion. A retry retains
its topic, source hash, reason, snapshot, seed and language even if the feed is unavailable.
A second worker cannot claim an already running slot. No timeout automatically steals running
work; reconcile the worker/provider journal before explicitly marking a failure and retrying.

Current uncovered favorites are selected randomly first. Newly observed uncovered favorites
outrank previously observed uncovered favorites, followed by uncovered public topics. Observations
are retained, so removing/re-adding an already observed topic does not make it artificially new.
Changes affect future slots; running selections stay fixed. Accepted/completed coverage is
at the topic level. Exhaustion stops selection instead of silently repeating an episode.

Dutch guitar is the benchmark; German is the next slot. The language flips only when a slot
completes with an exact accepted v3 build. Failure/retry preserves language. Default cadence is
one Monday 09:00 Europe/Berlin slot; no scheduled job is installed. The legacy preparation/release
GitHub jobs now have literal-false job guards and cannot become an alternative daily path simply
by setting the old `PRODUCTION_ENABLED` flag. Legacy release records are untouched.

## Manual preparation

```bash
# Validate a saved private snapshot and public topic file; no selection or provider calls.
.venv/bin/python3 scripts/weekly_v3.py --slot 2026-09-14 --experiments PATH_TO_PUBLIC_EXPERIMENTS --snapshot PATH_TO_PRIVATE_ENVELOPE

# After separate feed deployment/token setup authorization: one HTTPS read, no selection.
.venv/bin/python3 scripts/weekly_v3.py --slot 2026-09-14 --experiments PATH_TO_PUBLIC_EXPERIMENTS --fetch

# Explicit local selection only; never starts a renderer, TTS request, upload or publication.
DRY_RUN=false .venv/bin/python3 scripts/weekly_v3.py --slot 2026-09-14 --experiments PATH_TO_PUBLIC_EXPERIMENTS --snapshot PATH_TO_PRIVATE_ENVELOPE --select
```

The selector API is prepared and tested; there is intentionally no unattended production runner.
The CLI can currently resolve accepted coverage from the guitar benchmark bundles. Generalizing
coverage discovery to later v3 templates belongs to the post-acceptance production phase.
No local sample favorite list is silently substituted when production credentials are missing.

Validation: Python tests cover priorities, stale/missing/malformed/unknown inputs, exhaustion,
retry language and concurrent claim/selection. The Node harness under `scripts/mint-integration/`
uses mock queries to verify an 83-topic response, stable revision, method/auth failures, read-token
rejection by existing write authentication, sanitized errors and absence of history/DB calls.
