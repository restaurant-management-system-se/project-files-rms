# Integration contract and setup review

Review candidate dated 23 October 2026. Updated main is `9b4f49f` with #38/#39 merged; initial inspection used b171c48. Existing owner contracts are reused: `backend/docs/auth-security-contract.md` and the RMS-08/09 contracts on PR #38. Teammate agreement is pending. Posting this file does not approve a deviation.

## Shared configuration

| Boundary | Current rule | Owner and remaining action |
|---|---|---|
| Database | PostgreSQL, `DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT`; `accounts.User` is the only user model | Reuse #35 migrations and idempotent `seed_demo`; use a new empty disposable database when upgrading the old auth.User skeleton |
| Browser API | Same-origin JSON, `/api` prefix, no trailing slash, timezone-aware ISO timestamps | Each feature owner includes its own URLs; no cross-app view imports |
| Login | Cookie session, public registration/login require CSRF; login rotates CSRF | Reuse #36. Refresh `X-CSRFToken` after login; never send session IDs in URLs/logs |
| Authorization | 401 missing identity; 403 wrong role/CSRF; Customer owns own records | Reuse shared permissions/query filtering; feature owners derive ownership server-side |
| Errors | Auth currently returns DRF field errors or `detail`; booking candidate uses `code/message/details` | Clients render both as text; unified envelope and duplicate-registration 400 vs SAD 409 need team approval under PENDING-05 |
| Booking | Default 90 minutes, `[start,end)` intervals; POST uses table_id/start_at/party_size/idempotency_key | #38/#39 are merged into main. Customer-then-table locks and retries passed PostgreSQL tests; policy/full acceptance review remains pending |
| Menu/order | Public available menu grouped by one of four categories; checkout re-reads availability/price, computes totals in one transaction | Prasanna #18–24 owns endpoints/payloads and fixes. `/api/menu` and order POST/status are pending on main; do not code against guessed response schemas |
| Node | Separate process; no DB writes; Django commits before publishing | The harness supplies a Socket.io test client, not a production server. Authorized delivery, server startup, subscribe/event schema, session revocation and REST recovery remain RMS-18/19 |
| Sessions | 1800-second server idle boundary; session-status poll must not extend it | Existing auth clock seam reused in tests. Socket invalidation remains PENDING-06 |

Existing `backend/.env.example` is used without committing credentials. Python dependencies are pinned in `backend/requirements.txt`; Node uses `npm ci` with its committed lockfile. Test clocks/role fixtures belong only in the harness. Use normal PostgreSQL settings for concurrency evidence; SQLite settings cannot verify row locks.

## Setup findings

1. Main has complete migrations and an existing PostgreSQL 16 workflow. Combined main plus the shared harness passed all 63 Django tests on PostgreSQL 16.15 in run 39900859010, with no skips; Node fixture tests also passed. Its `postgres` job on main `b171c48` passed in run [39738102388](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/39738102388). PR #34/#35 are merged, but no human approval submission is visible on their review API; merge provenance is not proof of an independent review.
2. At baseline Node has a lockfile and `.env.example`, but no `index.js` and a failing placeholder test command. The harness follow-up supplies real Socket.io client tests against an explicitly labelled in-process fixture. Production startup remains a documented blocker; completed RMS-02 is not recreated.
3. This local environment maps only uid 0 (`/proc/self/uid_map`), has no PostgreSQL/container runtime, and cannot run PostgreSQL as a non-root user. PostgreSQL execution must be evidenced by the existing GitHub Actions service. Local SQLite checks are reported separately.
4. Menu browsing, cart, checkout, staff lifecycle, TLS/WSS, lockout, audit retention, browser compatibility, usability and load acceptance are pending. A full customer flow is blocked by these missing features.

## Integration procedure

Feature owners retain their branches and tests. Review a PR and record its exact SHA/check run first. After owner merge, fetch main and update only an integration branch. Run fresh migrations, seed twice, migration-drift check, all Django tests on PostgreSQL, Node tests and traceability validation. Keep failure logs, database/runtime versions and the precise source revision. Send failures to the owner through the linked issue/PR; do not quietly repair their branch or label blocked cases passed.

PR #38 is now merged into main 9b4f49f and already contains #39; do not cherry-pick #39 again. The CI integration helper merges current main into a disposable test checkout without pushing any owner branch. Raw evidence records the PR revision, main SHA and tested tree. GitHub returned no human review submission on #38, so independent review is not inferred from its merge.

## Demo steps

1. In an empty PostgreSQL development database, follow `backend/README.md`, install pinned requirements, migrate and run `seed_demo` twice. Demo accounts deliberately cannot log in. Create your own local administrator through `createsuperuser`.
2. Run Django. Run `cd realtime && npm ci && npm test` once the harness PR is applied to exercise the client fixture. `node index.js` remains blocked until the RMS-18 owner supplies the production server; this is not socket acceptance.
3. Register at `/register/`, log in at `/login/`, open `/account/`, `/api/bookings` and `/api/orders`, log out and verify protected access is rejected. No credentials need to be committed.
4. On main 9b4f49f or the combined test checkout, open `/book/`, search a future slot, confirm and observe a BK reference. A second customer requesting that interval gets a conflict/alternative; a retry with the same key returns the original record. Run PostgreSQL race tests for proof of locking.
5. Menu → cart → checkout → live tracking cannot yet be demonstrated on main. Keep the relevant canonical IT/ST/SV cases Not Executed until the owners' reviewed changes and deployment exist.

See `quality/README.md` for all requirement mappings and the exact Test Plan release gate. Review PENDING-01–07 in the existing deviation register; this supplement does not silently resolve them.
