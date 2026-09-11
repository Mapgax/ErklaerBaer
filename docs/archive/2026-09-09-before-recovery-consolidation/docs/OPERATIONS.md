# Operating procedure

Current production work follows [PRODUCTION_V3_PROMPT.md](PRODUCTION_V3_PROMPT.md).
The complete Dutch guitar benchmark is the first creative gate; coin, safari and weekly
production remain gated behind its explicit acceptance. Technical checks are not creative approval.

See [current implementation and blockers](V3_IMPLEMENTATION_STATUS.md),
[private weekly selection and feed](WEEKLY_V3.md), and [asset recovery](ASSET_RECOVERY_V3.md).
The selector/feed code is implemented and tested with mocks, but is not deployed or activated.
Default dry-run behavior is retained. All legacy automatic preparation/release jobs are disabled.
The previous operating text is preserved [as history](archive/OPERATIONS_pre_v3.md).

Before every paid call, read the persistent usage ledger. Keep uncertain submissions reserved
and recover their journals before retrying. A month change, resumed task or new v3 render does
not renew any allowance. Keep favorites, credentials and owner feedback out of provider calls,
galleries, code archives and public artifacts.

For local review builds use `scripts/build_v3_guitar.py`; its default reuses cached Chirp PCM.
The expressive path is explicit and token/dollar bounded. Use `scripts/validate_v3_bundle.py`
against the exact version directory before handing it over; it rejects stale inputs and checksums.
Current native-rim and expressive-voice blockers prevent completion of the creative review gate.
