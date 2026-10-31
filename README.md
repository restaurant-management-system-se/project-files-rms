# Restaurant Management System

A single-restaurant application built by Captain-King-2024, Noctowl-Abhay, AkulkrishnaMS and prasanna-p2006. Django/DRF owns business rules and PostgreSQL transactions; Node.js/Socket.io is the planned realtime delivery layer. Original requirements/design authorship is retained in the source documents.

## Implementation status

**Status reviewed 31 October 2026 against main `fa71e740ac1117fe57ac1be4c358d19aa2549dd0`.** The repository is still under integration and acceptance testing. An issue being closed or a PR being merged into another feature branch does not prove its code reached `main`.

| Present in this main revision | Remaining integration / acceptance |
|---|---|
| Database migrations and repeatable demo data (#35) | Staff booking management #44 was merged into a feature branch; absent from main |
| Customer registration, sessions, roles/ownership and CSRF (#36), login lockout (#45) | Audit #46, staff status #52 and live tracking #53 remain open |
| Availability, nearest alternatives, atomic confirmation and customer cancellation (#38, #39, #43) | Stale-cart #51 was merged into #50's feature branch; absent from main |
| Admin menu, public menu, cart and atomic checkout (#47–50) | Expanded harness/workflow #41/#42 merged into feature branches; absent from main while #40 remains open |
| Basic PostgreSQL foundation CI | HTTPS/WSS, reconnect, load/latency/restart/browser/human acceptance and complete CD remain pending |

**Later update during this session:** teammate-merged PR #40 advanced main to `566d0a8af49683e97eba02f00def91d03513dbe7`. The canonical RTM and #41 regression harness are now integrated (`quality/` and `backend/quality/`); #42's expanded workflow is still absent. The dated table above describes the earlier fa71e740 snapshot. Staff integration is now proposed in #58, reusing #44 and correcting booking view imports to the existing shared resource interface. Latest-main local integration checks passed 76 tests with 35 PostgreSQL-only skips, including the module-boundary check; 29 requirements / 58 canonical cases validate. Full deployment/human/browser acceptance remains pending.

The detailed [delivery status and evidence](backend/docs/RMS-32-delivery-status.md) records dependencies, original test heads, review gaps and demo limits. Captain's remaining work is scoped to #15 (usability), #16 (browser verification) and #17 (documentation), with a separate PR for each. Do not self-review, merge or close acceptance issues based on preparation alone.

## Repository structure

- `backend/`: Django project (`rms_backend`) and `accounts`, `booking`, `menu`, `orders` apps, migrations, templates/static assets and evidence in `backend/docs/`.
- `quality/` and `backend/quality/`: canonical traceability and regression harness, integrated through #40 during this session.
- `realtime/`: Node package manifests/client fixtures in main; the runnable Socket.io server is proposed in PR #53, not present here.
- `.github/workflows/`: PostgreSQL foundation checks and documentation reminder. PR #42 proposes the expanded workflow; PR #54 proposes production Django configuration, without a CD workflow.
- `Issues/Backlog/DEVIATION_REGISTER.md`: recorded decisions and pending clarifications; proposals are distinct from approvals.
- `SRS and Test Plan Details/`: source SRS and Test Plan.
- `Software Design And Architecture Specification/`: source SAD.
- `Test Cases related to Test Plan/`: additional source test cases. Folder names above are case-sensitive and match the repository.

## Local setup (Windows, Linux or macOS)

Use Python 3.12+ and PostgreSQL 16 to reproduce the foundation CI environment. Create a **new empty development database** through pgAdmin or `createdb`; keep any old database intact. From a fresh clone:

```bash
git clone https://github.com/restaurant-management-system-se/project-files-rms.git
cd project-files-rms
python -m venv .venv
```

Windows PowerShell uses `.venv\Scripts\Activate.ps1`; Windows Command Prompt uses `.venv\Scripts\activate.bat`; Linux/macOS uses `source .venv/bin/activate`.

```bash
python -m pip install -r backend/requirements.txt
cd backend
```

Copy `.env.example` to `.env` (`Copy-Item .env.example .env` in PowerShell; `copy .env.example .env` in Command Prompt; `cp .env.example .env` on Linux/macOS). Edit it locally: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST=127.0.0.1`, `DB_PORT=5432`, `DEBUG=True` and a random `SECRET_KEY`. Generate the key with `python -c "import secrets; print(secrets.token_urlsafe(48))"`, then paste it only into your local `.env`. Never commit credentials. The database must exist and be owned by the configured user before migration.

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Open http://127.0.0.1:8000/register/ to create a Customer, then `/login/`. Use `/book/` for search/confirmation, `/my-bookings/` for cancellation/history, `/menu/` for dishes and `/cart/` for checkout. `/` currently has no home page. Admin signs in at `/admin/` to maintain tables/provision Staff; `/manage/menu/` manages menu dishes. Staff booking/status interfaces require their owner PRs to reach main first.

`seed_demo` is development-only (`DEBUG=True`), atomic and repeatable; its demo accounts have **unusable passwords**. Create real local test accounts yourself; do not enable passwords on reserved `rms_demo_*` accounts. Preserve all committed migrations. The detailed [backend setup](backend/README.md) explains the custom-user/old-database boundary.

There is no runnable Node server in this main revision; do not run the old `node index.js` instruction. After reviewed #53 reaches the integration build, follow [its runtime contract](https://github.com/restaurant-management-system-se/project-files-rms/pull/53) for shared private key, internal URLs, exact public origin and a same-origin proxy. Node 22 is the feature's CI baseline. Node never writes business data. Akul's reconnect/CD and Noctowl's HTTPS/WSS work remain separate ownership.

These commands run a local development instance, not an implemented deployment pipeline. PR #54's Gunicorn/WhiteNoise/health configuration is still proposed; Gunicorn is a Linux server dependency. No public host, local self-hosted deployment runner or deployed HTTPS/WSS result is claimed.

## Verification

From `backend/`, with a disposable PostgreSQL database configured and a role allowed to create the separate test database:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test accounts booking menu orders --verbosity=2
python verification/check_documentation.py
```

The test runner creates/destroys `test_<DB_NAME>`. Do not point tests at a production database. For fast local regression only: `python manage.py test accounts booking menu orders --settings=rms_backend.test_settings`. SQLite cannot verify row locking, concurrency or checkout and must not be used to run the application.

The usability protocol and browser suite are in the separate #15/#16 PRs; their execution gaps must remain visible. Akul owns the canonical RTM/harness (#40/#41 now integrated; #42 workflow pending); documentation does not replace its planned cases with automatic “Passed” statuses.

## Source documents and governance

- [SRS (PDF)](SRS%20and%20Test%20Plan%20Details/SRS/SRS-_Restaurant_Management_System.pdf)
- [Test Plan (PDF)](SRS%20and%20Test%20Plan%20Details/Test-Plan/Test_Plan_Restaurant_Management_System_SE.pdf)
- [SAD (PDF)](Software%20Design%20And%20Architecture%20Specification/SAD-%20Restaurant%20Management%20System.pdf)
- [Additional test cases (PDF)](Test%20Cases%20related%20to%20Test%20Plan/Test_Cases-Restaurant_Management_System.pdf)
- [Deviation register](Issues/Backlog/DEVIATION_REGISTER.md)
- [Dated status snapshot](backend/docs/repository-status-2026-10-31.json) and [unaltered source hashes](backend/docs/source-document-hashes.json).

The user selected Sprint 1 **19–23 October 2026** and Sprint 2 **26–31 October 2026**. These dates supersede earlier deferred-planning notes for this working session, but the Project still exposes no formal Sprint allocation field. Human acceptance, team-wide sprint outcomes, videos and a release freeze have not been evidenced. Do not infer historical burndown values from today's issue state.
