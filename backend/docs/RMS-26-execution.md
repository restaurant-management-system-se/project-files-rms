# RMS-26 executed checks — 31 October 2026

Base: main `fa71e740ac1117fe57ac1be4c358d19aa2549dd0`. UI changes are in the accompanying PR. No backend model/API/auth changes.

- Python 3.12 / pinned backend requirements: Django system check passed; migration drift check passed (SQLite test setting); JavaScript syntax and git diff whitespace checks passed.
- Actual local regression: `python manage.py test accounts booking menu orders --settings=rms_backend.test_settings --verbosity=1`: 93 discovered; 67 passed, 26 PostgreSQL-only skipped; 1.197s.
- This environment's PostgreSQL launch failed before application tests: the container disallows switching to an unprivileged PostgreSQL user (`runuser: cannot set groups: Operation not permitted`). This is not a database concurrency pass.
- Optional Playwright 1.64.1 package installed, but its Chromium download returned an invalid/truncated ZIP. No local browser-engine or browser-rendering pass is claimed.
- The existing repository PostgreSQL workflow runs on this PR; record its exact run/head/outcome separately after it finishes. Historical booking concurrency runs belong to their original heads, not this UI revision.
- ST_11: T1, T2, T3 **Not executed**. The neutral protocol and empty results table are in `RMS-26-usability.md`.

Do not mark QA-1 or #15 complete until the human results satisfy the criteria. Independent review/owner merge remain required.
