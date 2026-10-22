# RMS-03 verification and traceability

Issue: #10, [RMS-03] Create database migrations and reusable demo data.
Baseline: main dbee0cdb9a76e06b5d7ee2ea1c91649854c91459; SAD section 6; SRS section 7 and QA-3; approved DEV-01 and DEV-06.

| Acceptance criterion | Implementation | Evidence |
|---|---|---|
| Six core entities and SAD keys/checks | Four app model files and initial migrations | Constraint, foreign-key, uniqueness and historical-price tests |
| Three roles, varied capacities, four categories, available/unavailable dishes and representative bookings/orders | `accounts/management/commands/seed_demo.py` | Seed fixture contents and calculated totals verified |
| Repeat seeding without duplicate records or real credentials | Atomic get-or-create seed, reserved identities, unusable passwords | Full before/after records match; collision rollback and production refusal tested |
| Restricted staff provisioning and table maintenance | Admin-only user and table administration; customer-only public manager | Admin form creates Staff and changes capacity/active state; Staff/Customer requests denied; elevated create_user rejected |

Executed locally on Python 3.12.14 / Django 6.1.2, 22 October 2026:

- Dependency installation from existing pinned requirements: PASS.
- `python manage.py test accounts booking menu orders --settings=rms_backend.test_settings`: 10 tests PASS using a fresh migrated in-memory SQLite test database.
- `python manage.py makemigrations --check --dry-run --settings=rms_backend.test_settings`: no changes detected.
- `python manage.py check`: no issues.

PostgreSQL is configured as the application's default. A local PostgreSQL server is unavailable in the execution environment; PostgreSQL migration/test execution is not claimed here. A dedicated GitHub Actions workflow provisions PostgreSQL and runs the same suite; its actual run result is recorded in the PR. IT_01 (booking) and IT_08 (checkout) remain pending feature implementation, including atomicity/concurrency tests. Runtime endpoints, cross-row business rules, events and UI are outside RMS-03.

Review note: selecting a custom user before initial feature migrations avoids later swapping of the auth model. Coordinate Noctowl's authentication implementation against `accounts.User`. No existing source document has been silently rewritten; this note records the implementation mapping and test evidence only.
