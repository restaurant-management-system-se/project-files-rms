# Shared regression harness

RMS-30 / #31 builds on RMS-29, completed RMS-02 #34 and database #35; no production feature is recreated. Feature owners keep their implementations/tests. `backend/quality` is test support, not a production Django app. Python dependencies and all migration files are reused unchanged.

## Reproduce

Install `backend/requirements.txt` in a fresh Python 3.12+ virtual environment. Use a disposable PostgreSQL database and normal environment settings from `backend/.env.example`. The test user needs CREATEDB. Existing `rms-database-tests.yml` supplies PostgreSQL 16 in CI; no second database service is introduced.

From the repository root:

```bash
python quality/check_traceability.py
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
python manage.py seed_demo
python manage.py seed_demo
python manage.py test accounts booking menu orders quality.test_harness --testrunner=quality.runner.EvidenceRunner --verbosity=2
cd ../realtime
npm ci
npm test
```

Use `--settings=rms_backend.test_settings` only for local SQLite smoke. Those results do not prove PostgreSQL locking, migration deployment, load or browser behavior. The explicit `quality.test_harness` label avoids confusion with the root documentation directory. Keep execution serial; the evidence runner rejects parallel mode.

`test-results/django.json` records exact executable name, mapped requirement/planned IDs, scope, outcome, duration, UTC window, source revision/dirty state, Python/Django and database versions. `quality/executables.json` provides external mapping for owner-authored tests without modifying their code. Tests without a canonical correspondence retain their executable ID and empty canonical IDs; no association is invented. Database/seed support cases may have no numbered requirement. Newly merged features must add their executable mapping in their PR.

`SessionClient` enforces real CSRF and obtains fresh tokens through the merged auth endpoint. `role_users` creates isolated test-only Customer/Staff/Admin users through the model, without enabling reserved demo accounts. `auth_clock` patches the existing auth time seams and restores them automatically. H_02 exercises 1799/1800-second idle behavior. Existing owner tests cover 1801 seconds, replay, CSRF and permissions.

H_01 deliberately runs one passing, one failing and one skipped child test in memory and verifies that the reporter distinguishes them. That expected child failure is a reporter self-check, not an application defect or a fabricated application test pass. SR_01 scans all Python files in the four apps for direct cross-app view imports.

## Node test client

`realtime/test-client.js` supplies a Socket.io connect/subscription/event-deadline client with credentials support and no reconnection loop. `test/client.test.js` exercises it using a loopback, in-process **synthetic fixture server**, including a rejected handshake and missing-event timeout. These H_NODE tests establish the client harness only. They are not IT_06/07, WSS, real ownership/session revocation or PERF-2 evidence. No production `index.js` is added; the existing startup gap remains with RMS-18.

## Evidence and integration

Use [REPORT_TEMPLATES.md](REPORT_TEMPLATES.md) for manual execution, defects, security and summary reports. Skipped, blocked, expected-failure and unmapped cases never become canonical passes. The machine inventory retains full source procedures as Not Executed unless a complete procedure has separate evidence. Run artifacts are ignored by git and uploaded by the RMS-31 CI extension even when tests fail.

Main currently supports register → login → owned resource reads → logout. Booking candidate #38 (which contains #39) may be tested in an isolated integration checkout; it is not merged-main evidence. Menu/cart/checkout/status and production realtime remain blocked by the feature owners' pending work. Review gates, scope and demo steps are in [INTEGRATION.md](INTEGRATION.md).
