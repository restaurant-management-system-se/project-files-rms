# RMS-27 / #16 — browser and viewport verification

Owner: Captain-King-2024. QA-4 / ST_13. Separate PR depends on RMS-26's booking UI, without changing other owners' models/APIs. Proposed Sprint 2: 26–31 October 2026; baseline issue allocation remains unassigned until the team records it.

## Automated regression

`verification/browser_smoke.py` uses real rendered forms, session/CSRF, a live Django server and PostgreSQL. It covers registration/login/logout, Customer denial of menu management, booking confirmation/cancellation with database assertions, public menu -> cart -> committed checkout, invalid booking inputs and Admin menu creation. It checks booking-page horizontal overflow at 1280x800, 390x844 and 320x568 and reports actual engine version, build, timestamp, database and per-case outcome. Screenshots contain only generated disposable test data. Credentials are generated in memory, never committed or written to reports. Tests run in Django's isolated `test_<DB_NAME>` database and do not target a deployed service or real user data.

From `backend/`, with PostgreSQL configured in `.env` and a user permitted to create test databases:

```bash
python -m pip install -r requirements.txt -r verification/requirements.txt
python -m playwright install --with-deps chromium firefox
RMS_BROWSER=chromium python manage.py test verification.browser_smoke --verbosity=2
RMS_BROWSER=firefox python manage.py test verification.browser_smoke --verbosity=2
```

Windows PowerShell: set `$env:RMS_BROWSER='chromium'`, then run the Python test command. The `--with-deps` system dependency installation is for Linux CI; Windows normally uses `python -m playwright install chromium firefox`. For genuine installed Chrome/Edge, choose `chrome` / `msedge`; no branded browser is silently substituted with bundled Chromium. Set `RMS_EXPECTED_VERSION` to require an exact installed version. Firefox automation uses Playwright's patched Firefox; verify actual stable Firefox versions manually below.

`RMS_BROWSER_RESULTS` optionally controls the evidence directory (default `../test-results/browser`). Missing binaries fail the opted-in suite. SQLite fails closed. Ordinary application regression does not discover this opt-in module.

The narrowly scoped `rms-browser-smoke.yml` workflow is proposed QA automation for this issue; it does not replace Akul's CI harness or CD ownership. Its PostgreSQL service follows the existing foundation pattern. It produces per-case JSON/screenshots and raw logs for 30 days on success/failure. It tests the checked-out PR revision; no automatic merges, secrets, deployments or teammate branch edits.

## Formal ST_13 gate — NOT completed by bundled engines

On the actual execution date, identify the latest **two stable released versions** of each branded browser from official vendor release pages. Record full versions/build, platform and source URL with retrieval time. Beta/dev/nightly/Playwright revision numbers do not meet this requirement. A newer stable release invalidates a stale “latest two” selection; recheck at execution.

Official version sources: https://chromereleases.googleblog.com/search/label/Stable%20updates ; https://www.mozilla.org/firefox/releases/ ; https://learn.microsoft.com/deployedge/microsoft-edge-relnote-stable-channel . Obtain installers through official vendor channels or a team-approved browser service. Do not downgrade a personal browsing profile; use isolated test machines/profiles.

Each cell must execute at desktop 1280x800 and mobile-sized 390x844 (also inspect 320x568 for booking). Resizing a desktop browser is viewport coverage, not evidence of a physical mobile device or mobile browser.

| Browser | Version selection | Exact version / OS / source date | Auth | Menu/cart/checkout | Book/cancel | Staff bookings/status | Live tracking/reconnect | Rendering / defects | Gate |
|---|---|---|---|---|---|---|---|---|---|
| Chrome | Latest stable | Pending execution | Not executed | Not executed | Not executed | Blocked | Blocked | Not executed | Not executed |
| Chrome | Previous stable | Pending execution | Not executed | Not executed | Not executed | Blocked | Blocked | Not executed | Not executed |
| Firefox | Latest stable | Pending execution | Not executed | Not executed | Not executed | Blocked | Blocked | Not executed | Not executed |
| Firefox | Previous stable | Pending execution | Not executed | Not executed | Not executed | Blocked | Blocked | Not executed | Not executed |
| Edge | Latest stable | Pending execution | Not executed | Not executed | Not executed | Blocked | Blocked | Not executed | Not executed |
| Edge | Previous stable | Pending execution | Not executed | Not executed | Not executed | Blocked | Blocked | Not executed | Not executed |

For each browser/viewport: register a unique Customer, login/logout; browse four categories and unavailable-item exclusion; book tomorrow 19:00 and cancel; checkout with snapshots; use a distinct Staff profile for search/manual booking/cutoff override/status; open owned live tracking and change status from Staff; test reconnect/stale-event recovery; confirm cross-customer denial. Record expected/actual, exact SHA, screenshot/log references and linked defects. Keep unsuccessful results and repeat after fixes.

## Actual execution and blockers, 31 October 2026

Local browser binary installation failed (invalid/truncated ZIP), so no local engine or branded-browser result is claimed. Local backend SQLite results are recorded by RMS-26, not substituted for browser evidence. GitHub workflow results will be linked after execution, including failures. No first-time-human usability result is implied.

At main `fa71e740ac1117fe57ac1be4c358d19aa2549dd0`, Staff booking UI from #44 is not integrated despite that PR's merge into a feature branch. Staff order status #52 and realtime #53 remain open; reconnect #26 belongs to Akul and has no implementation PR. HTTPS/WSS #6 and deployment CD remain pending. All those flows stay blocked in this formal matrix until owners integrate them and a deployment is available. No teammate implementation is taken over to manufacture a green ST_13 result.

Keep #16 open / In Review and the PR draft until the six real-version cells, required flows and independent review are complete.
