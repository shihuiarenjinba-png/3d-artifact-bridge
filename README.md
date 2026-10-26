# 3d-artifact-bridge

Shared **offline, read-only intake gate** for three production lanes:
`APP -> AI-App-Factory`, `GAME -> AI-Game-Factory`, `GAME_3D -> 3d-game-factory`.

This repository does **not** hold game builds. Artifacts stay in an authorized external store; only their HTTPS location and claimed SHA-256 are included in a manifest. It does **not** fetch artifacts or confirm the claimed hash. Claims marked PASS do not prove anything until independently verified by Windows QA.

```bash
python -m unittest discover -s tests -v
python bridge.py examples/valid-review-candidate.json
```

Possible statuses: BLOCKED (bad structure or conflicting lane), HOLD (unfinished QA), REVIEW_CANDIDATE (complete claims **only**, requiring independent evidence verification). The tool never returns SUBMITTED, CERTIFIED or RELEASE_READY, never calls Partner Center, and never performs uploads.

Required manifest fields: `schema_version`, `request_id`, `product_type`, `source_factory`, `repository_full_name`, `source_sha`, `artifact` (HTTPS URI, SHA-256, bytes, MSIX/MSIXVC type), `qa` (build/automated/human/licensing and human approval reference).

**HOLD** until: provisioner contracts from local team are received; external immutable artifact retention and hash verification are implemented; Windows-all-auto adapter is written and tested against its actual schema; operator QA and packaging are verified. No live integration has been claimed.
