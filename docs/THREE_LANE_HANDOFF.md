# APP, GAME, GAME_3D — intake isolation

Factory origin and declared product type MUST match:
- APP <-> AI-App-Factory <-> Repository-Provisioner-app
- GAME <-> AI-Game-Factory <-> Repository-Provisioner-game
- GAME_3D <-> 3d-game-factory <-> Repository-Provisioner-3D

1. Factory proposes an explicit private, dry-run request with unique request ID. Local Provisioner contract is not yet delivered. The bridge tests only compatibility, not identity/permissions.
2. Provisioner replies with DRY_RUN/HOLD or verified information after live creation. A claimed live result is always a **candidate** pending authenticated GitHub readback (exact URL, repo ID, source HEAD, template and visibility).
3. Development is independent; App/Game existing Factories currently keep products in their own repository. Per-product repository migration is NOT done here and must never silently copy unreviewed products.
4. Windows-build and QA receipts require their own verification and human approval. `bridge.py` checks structure but does not verify bytes or claims.
5. For Windows-all-auto, the queue must be partitioned by product type with independent concurrency/quotas, and all 3 lanes must share immutable request_id, repo+commit SHA, artifact SHA-256 and approval reference.
6. No partner-center live upload, signing or Store certification is authorized from these offline checks. Unknown schema/status → HOLD/BLOCKED. No auto-deletion of approved assets; ephemeral runner data only.

**HOLD until**: reviewed local Provisioner handoffs + secret permissions + template readiness, durable project state with single-writer lease/CAS, actual Windows GPU worker for 3D, authenticated artifact evidence, and actual Windows-all-auto adapter contract with end-to-end verification.
