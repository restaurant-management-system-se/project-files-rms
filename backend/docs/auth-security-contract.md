# Authentication and scoped security contract

Review candidate for RMS-04 (#2), RMS-05 (#3), RMS-06 (#4), auth-scoped RMS-21 (#7) and RMS-22 (#8). Based on main `738b361` with RMS-03 PR #35 merged. `accounts.User` and every existing migration are preserved. RMS-01 is already closed via PR #33. The Project still states sprint planning deferred; this change does not assign sprint dates or claim a formal allocation.

## Baseline review

SRS REQ-12/13/14 and SEC-1/3/4/5/8, SAD sections 4, 5.3 and 7, Test Plan Appendices A–D, the additional Test Cases document, issues and Project were inspected on 22 October 2026. No open PR was returned by the repository PR query at the start of work.

The merged register marks DEV-01–07 Approved: Django owns database writes, customer booking cancellation has a 30-minute cutoff, staff override needs a reason/audit trail, missing authentication is 401, wrong role is 403, menu/availability reads are public, ST_09/ST_10 are canonicalised, payment processing is excluded, and sprint allocation remains unset. The register's `[cite: N]` markers have no source map; merger evidence is PR #33, not an invented independent approval record.

Unresolved items are recorded in the governance follow-up. This implementation uses existing email-required storage, optional phone login and safe output encoding. Team approval of phone-only registration, phone canonicalisation, output-versus-storage wording, order-cancellation exceptions and latency wording is not claimed.

## API contract

All paths below have **no trailing slash**. Use JSON and same-origin cookies (`credentials: 'same-origin'` in fetch). No Bearer/JWT interface is implemented. Errors use DRF's field-error objects or `detail`; clients must render these as text, never HTML. A future shared error-envelope change needs coordination.

| Method | Path | Access and result |
|---|---|---|
| GET | `/api/auth/csrf` | Public. Returns `{csrfToken}` and CSRF cookie; not a session heartbeat. |
| POST | `/api/auth/register` | Public **with CSRF**. `{name,email,phone?,password}` → 201 profile. Creates Customer only; does not log in. Unknown fields (including role flags) rejected. |
| POST | `/api/auth/login` | Public **with CSRF**. `{identifier,password}` → 200 `{user,csrfToken}`. Identifier is case-insensitive email or exact stored phone. Invalid/inactive accounts → generic 401. |
| POST | `/api/auth/logout` | Authenticated + CSRF → 204. Server session flushed; old cookie cannot authenticate. GET does not log out. |
| GET | `/api/auth/session` | Authenticated → `{user,idleExpiresAt}`. Does **not** advance inactivity deadline. Missing/expired identity → 401. |
| GET | `/api/bookings`, `/api/orders` | Authenticated. Lists filtered to Customer's own records; Staff/Admin may read all. Results are currently bounded to first 100 by ID; pagination and workflow filters belong to the feature owners. |
| GET | `/api/bookings/{id}`, `/api/orders/{id}` | Owner or Staff/Admin. Existing non-owned ID → 403; absent ID → 404. Responses omit customer contact information. |

Profile fields: `id,name,email,phone,role`; passwords/hashes/permission flags are never returned. Names are capped at 60 characters. Email is required by the agreed model and lowercased. Phone is optional, 7–15 digits with an optional leading `+`; no country code is inferred or old data rewritten. Different national/international representations are not yet canonicalised. Passwords accept 8–128 characters subject to Django's common/numeric/similarity validators. New public users get generated internal usernames; public login uses email/phone. Django admin still accepts the administrator's username.

Registration checks identifiers and handles a database uniqueness race with a safe 400. Passwords use Django `create_user`, password validation, and PBKDF2-SHA256. Equal passwords have independent salts. Application code does not log request bodies or credentials; operational proxy/debug logging must also avoid request-body logging.

## Cookie and CSRF flow

1. GET `/api/auth/csrf` and retain its `csrfToken`.
2. Send `X-CSRFToken` on **every** POST/PUT/PATCH/DELETE with the same-origin cookie.
3. After login, replace the token with the returned `csrfToken` (Django rotates the CSRF secret and session key).
4. On 401, show login; on 403, show a permission/CSRF failure. Retrying writes automatically is not recommended.

DRF normally skips CSRF for anonymous requests; `SessionAPIView` explicitly checks public registration/login too. Missing or invalid CSRF for authenticated unsafe requests gives 403 and no mutation. Missing authentication on protected APIs gives 401 before permission-specific handling (approved DEV-03). Form pages use Django's CSRF middleware. Form CSRF failures are 403, and form logout requires POST.

Session cookies are HttpOnly and SameSite=Lax; with `DEBUG=False`, session and CSRF cookies are Secure. Default local development (`DEBUG=True`) supports HTTP localhost. HTTPS/TLS termination, real deployed cookie inspection, secrets and allowed origin configuration remain RMS-20. Do not deploy debug mode or use test settings.

## Idle expiry and pages

`IdleSessionMiddleware` runs after Django authentication. At `now - last_activity >= 1800`, Django logout flushes the server-side session. Ordinary authenticated activity resets both the idle timestamp and session expiry; session-status polling does not. A Django-admin-created session acquires an idle deadline on its first authenticated request. The browser's session cookie age is 1800 seconds as an additional limit.

`/register/` and `/login/` provide labelled forms and inline errors without echoing passwords. Successful registration takes the user to login; successful login opens `/account/`. The account page safely escapes the stored name, displays the role and resource links, and provides a CSRF-protected logout form. Missing/expired account access returns a clear 401 page with a login link. Account/auth responses are not cached.

## Permissions and integration owners

| Operation | Customer | Staff | Admin | Integration owner |
|---|---|---|---|---|
| Menu read / availability search | Public | Public | Public | Prasanna / Captain |
| Menu mutation | Denied | Denied | Allowed subject to validation/history rules | Prasanna |
| Booking/order list or detail | Own only | All permitted operational records | All | Read boundary implemented here |
| Own booking cancellation | Owner + time rule | Override + reason/audit | Override + reason/audit | Captain |
| Booking creation | Own | On behalf, validated customer | On behalf, validated customer | Captain |
| Order checkout | Own | On behalf, validated customer | On behalf, validated customer | Prasanna |
| Order status mutation | Denied | Allowed lifecycle transitions | Allowed lifecycle transitions | Prasanna |
| Booking/order hard delete | Denied | Denied | Denied in normal API flows | Shared ownership guard denies DELETE |
| Staff-account provisioning | Denied | Denied | Existing Django admin | RMS-03 existing functionality |

Feature owners must use global session authentication plus `IsRestaurantAdmin` for menu mutations, `IsStaffOrAdmin` for override/status actions, and `IsOwnerOrStaffAdmin` **plus** `owned_queryset` for customer-owned resources. The ownership permission denies DELETE even if a future handler is added. It does not implement time rules, audits, status transitions or create-time ownership assignment: always derive customer ownership from `request.user` for Customers; permit a validated customer selection only for Staff/Admin. Never copy arbitrary submitted role/customer fields into models. Do not add `csrf_exempt` or `AllowAny` to mutation endpoints.

No feature app imports another feature app's views. Global API defaults deny anonymous access. Future public menu/availability endpoints need an explicit read-only public exception; they are not fabricated here. Existing Django admin screens retain their RMS-03 Admin-only policy; Django admin's standard login redirects are unchanged.

Captain is `Captain-King-2024`, Prasanna is `prasanna-p2006`, and Akul is `AkulkrishnaMS`, verified from repository contributors and Project ownership. A coordination request is posted on #2. This records a proposed integration contract; their agreement has not been assumed.

## WebSocket blocker

The `realtime` directory currently has package manifests but no server or authenticated sockets. No working privileged WebSocket session is created by this branch. RMS-18/19 owners must implement a Django-backed session/ownership check, reject invalid/revoked/idle sessions, disconnect promptly on logout/expiry, and prevent background checks from resetting inactivity. Do not issue a long-lived standalone token that survives Django logout. Node must not own business writes or expose raw session IDs in URLs/events. End-to-end socket revocation tests remain pending; RMS-06 is not claimed complete across sockets.

## Verification executed 22 October 2026

Python 3.12.14; pinned Django 6.1.2 / DRF 3.18.3 installed unchanged. Commands run from `backend/`:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run --settings=rms_backend.test_settings
python manage.py test accounts booking menu orders --settings=rms_backend.test_settings --verbosity=2
```

Actual result: system check clean; no migrations detected; **35 tests passed**, including 10 existing foundation tests and 25 new auth/ownership/security tests. SQLite is a fresh migrated in-memory test database. The focused hash test overrides the fast test-only hasher with real PBKDF2-SHA256 and verifies differing salts. The existing PostgreSQL CI workflow runs this suite automatically for backend PR changes. A local PostgreSQL server is unavailable. GitHub Actions run [39735711074](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/39735711074) subsequently passed against PostgreSQL 16.15 for committed head `35b0e1c4188fe556f048583d9b85967b48268f63`: fresh migrations, both seed runs, no model drift, and all 35 tests passed in 15.972 seconds. The job logs were inspected. A separate checkout of that head also passed all 35 SQLite tests and all 18 uploaded files byte-matched the tested source. Deployed HTTPS/browser and WebSocket acceptance remain pending.

| Mapped cases | Actual scoped evidence | Remaining coverage |
|---|---|---|
| UT_17/18/19/22, IT_10, SV_01 | Customer creation, duplicate email/phone, concurrent duplicate handling, seven/eight-character boundary, real PBKDF2 salts, successful/failed/inactive email/phone authentication, no password response or captured application-log disclosure | External proxy/log audit |
| IT_09, ST_08/14, SV_03 | Customer/Staff/Admin/anonymous API guard matrix, filtered lists, own/other IDs, denied hard delete and unchanged records | Feature mutation integration and full browser flows |
| UT_20, SV_10 | Controlled clock at 1799/1800/1801 seconds, reset by activity, polling not a heartbeat, expiry/logout old-cookie replay rejected | Deployed clock and WebSocket disconnect |
| SV_09 | Test response Secure/HttpOnly/SameSite/max-age flags | Actual HTTPS deployment/browser inspection |
| SV_04/05 | SQL-like login rejected safely; malformed inputs return 400; stored script-like name escapes in rendered account HTML; no raw HTML insertion | Booking/menu/staff views, scanner/browser execution checks |
| SV_06 | Anonymous auth CSRF, authenticated logout missing/invalid/valid CSRF, hostile Origin and old CSRF rejected, shared API guard across POST/PUT/PATCH/DELETE | All future feature mutation endpoints |
| ST_07 | Django client sign-up → login → account → logout, inline errors, no password redisplay | Human/browser acceptance demo |

RMS-05/06/21/22 have cross-module acceptance criteria that remain pending feature integration/review. Lockout is separately tracked under RMS-07; audit logging/retention under RMS-23. No test pass is claimed for absent workflows.

## Demo for teammate review

1. Install requirements, configure an empty PostgreSQL database, and run `python manage.py migrate` using the existing setup instructions.
2. Run `python manage.py runserver`. Open `/register/`; submit a seven-character password and see the inline error. Register with your own test email and a compliant password.
3. Log in at `/login/` using email, then phone if supplied. Open `/account/`, `/api/bookings`, `/api/orders`. A new customer has empty lists.
4. Try a second customer against the first customer's existing resource ID: expect 403. Use provisioned Staff/Admin accounts to verify the role matrix.
5. Use the logout button, then revisit `/account/`: 401 with a login link. Replaying the old session cookie must fail.
6. Run the automated suite for exact 30-minute boundaries and missing/invalid/valid CSRF without waiting 30 minutes. Before deployment acceptance, repeat the real HTTPS cookie and socket checks.

Issues stay open/In Review until a teammate reviews and an owner merges. No author self-review or merge is performed.
