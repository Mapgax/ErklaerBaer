# Dependency review

> Current v3 implementation: [status and remaining gates](V3_IMPLEMENTATION_STATUS.md),
> [weekly feed/queue](WEEKLY_V3.md), [asset backup/recovery](ASSET_RECOVERY_V3.md).
> The Dutch guitar working render exists, but native rim repair and expressive narration are
> blocked. Legacy daily instructions below are historical and disabled; they are not an
> alternative production path. V3 creative acceptance has not been granted.


## Approved v3 direction

Retain the current compositor and official Rive runtime; add no generative-video provider or hosted
asset database. Trial Google Cloud Gemini 2.5 Flash TTS through the existing provider, verifying SDK,
language/voice support and token-aware spending before calls. BFL produces reusable collage artwork;
Rive authors motion; local manifests/HTML index assets. Review any required dependency update for
maintenance, licensing and security. Current approved details: [v3 prompt](PRODUCTION_V3_PROMPT.md).

The project intentionally avoids a web framework, database, generative-video service, audio
editing suite, and browser automation. `requirements.lock` fixes the complete Python 3.12
environment; `pyproject.toml` records compatible direct-dependency ranges.

## Direct production dependencies

| Package | Purpose | License family | Maintenance and supply-chain note |
|---|---|---|---|
| Anthropic SDK | Structured writer and independent review calls | MIT | Official vendor SDK; network data boundary is enforced before the call. |
| Google API Python client | YouTube Data API | Apache-2.0 | Official Google client; broad transitive dependency tree. |
| Google Auth OAuthlib | Local OAuth consent | Apache-2.0 | Official Google integration; refresh token is sensitive. |
| Google Cloud Text-to-Speech | Chirp narration | Apache-2.0 | Official Google client; service-account JSON is sensitive. |
| Pillow | Drawing, typography, thumbnails | HPND-style permissive | Mature project; malformed external images are not accepted as input. |
| NumPy | Audio and deterministic texture calculations | BSD-3-Clause | Mature project; native wheels increase supply-chain surface. |
| imageio / imageio-ffmpeg | Frame encoding and bundled FFmpeg | BSD-2-Clause | `imageio-ffmpeg` downloads a platform binary wheel; review on upgrades. |
| Pydantic | Strict source, storyboard, and catalog schemas | MIT | Mature project; schema validation is a boundary, not sanitization for execution. |
| `@rive-app/canvas-advanced` 2.42.0 | Occasional local `.riv` to transparent PNG bake | MIT | Official Rive runtime, isolated under `scripts/rive-bake`; it is not loaded by daily production. The helper disables Rive CDN loading and serves only on loopback. Review the pin and npm advisories before upgrading. |

Pytest and Ruff are development-only. The resolved environment also includes networking,
cryptography, protobuf, and gRPC packages required by the official SDKs. Their presence is the
main residual dependency surface.

## Upgrade procedure

1. Review security advisories, changelogs, repository activity, and license changes for direct
   dependencies.
2. Resolve a fresh Python 3.12 environment and replace every exact version in
   `requirements.lock`.
3. Run Ruff, the full offline suite, golden-frame comparison, and a private API pilot.
4. Inspect `pip check` and the dependency diff before merging.

Exact pins prevent accidental version drift but do not cryptographically pin distribution files.
Adding cross-platform hashes is worthwhile hardening once the deployment platforms are fixed;
hashing only the current macOS wheels would break the Ubuntu GitHub runner and create a false
sense of portability.

The GitHub workflows currently use the maintained major-version tags for `actions/checkout` and
`actions/setup-python`, rather than immutable commit SHAs. This is a residual workflow
supply-chain risk. Pin both actions to reviewed full commit SHAs before treating the automation as
high-assurance infrastructure, and let Dependabot propose explicit updates.

The Rive bake bridge is intentionally a one-off authoring dependency. It serves the explicitly
selected local `.riv`, official runtime module, WASM, and a token-bearing configuration from
`127.0.0.1`; frame POSTs are checked for Host, Origin, token, action, index, dimensions, RGBA mode,
and size. The browser performs no external runtime or asset fetch. Generated PNG sequences become
ordinary local inputs to the existing Pillow renderer.
