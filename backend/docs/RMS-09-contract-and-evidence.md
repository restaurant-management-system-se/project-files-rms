# RMS-09 atomic confirmation and demonstration

Depends on RMS-08 and merged RMS-03 (#35); shared permissions come from merged RMS-05 PR #36. This branch proposes Customer self-booking only. Staff/Admin on-behalf booking is RMS-11; no teammate issue or ownership was taken over. Noctowl-Abhay published the session/permission contract on #2; this issue reuses its merged implementation. Nearest-slot policy and peer review remain pending. Keep this PR unmerged until its dependency, PostgreSQL checks and teammate review are complete.

## Contract and transaction

`POST /api/bookings` with JSON `table_id`, timezone-aware `start_at`, integer `party_size`, and `idempotency_key` (1–128 letters/digits/underscore/hyphen). No customer/status/end-time fields accepted. Customer comes exclusively from the authenticated active Customer account. No session => 401; wrong role => 403; cookie session without valid CSRF => 403. Login/registration, shared permissions and idle expiry remain RMS-04/05/06. The existing shared permission/authentication boundary is reused; a booking-only role check limits this issue to Customer self-booking.

PostgreSQL is mandatory (503 on another database). Transaction locks the customer row, then the restaurant table row. Customer lock serializes same-customer retry keys across tables. Existing key + identical normalized payload returns persisted booking with 200, including after its start; changed payload => 409 IDEMPOTENCY_CONFLICT. Keys are scoped per customer and retained durably in separate BookingRequestKey, leaving RMS-03 User/Table/Booking field definitions intact.

For a new request, recheck future timestamp, table existence (404), active state, capacity, and confirmed overlaps: `existing.start < requested.end AND existing.end > requested.start`. Save Booking and retry metadata in the same durable atomic block. A failure rolls back both. Only after commit return 201, BK-<primary key> reference, status, current customer, table, party and interval. Table conflicts return 409 TABLE_UNAVAILABLE with fresh tables/nearest alternative and suggested_start_at. Availability is advisory; alternatives can also change before confirmation. All later booking mutation services must use the same customer-then-table lock order and table lock protocol. Direct ORM writes bypass service protection; the SAD's optional exclusion constraint is not added here.

The server computes end_at using the same configurable duration as search. Retry payload records requested fields, so an already successful retry preserves its original end even if configuration changes later. There is no new generic list/detail API or staff/cancellation implementation.

## Current integration and evidence (22 Oct 2026)

Rebased on main b171c48 with merged authentication PR #36 and governance PR #37. BookingView extends the existing BookingReadView, preserving its customer-filtered GET and protected detail routes. POST reuses global CookieSessionAuthentication and the existing SessionAPIView CSRF/idle behavior through OwnedResourceView. No shared auth source or established entity field is changed. Customer-only POST rejects Staff/Admin here; on-behalf handling stays RMS-11. Error display accepts shared `detail` responses as text.

Pinned Python 3.12.14 / Django 6.1.2. The combined SQLite suite discovered 59 tests: **47 passed, 12 PostgreSQL-only skipped**, in 1.198s. Local API/template smoke was 0.0048s. System check, migration consistency, JavaScript syntax and git diff whitespace checks passed. PostgreSQL-only tests are not claimed passed locally. The existing PostgreSQL 16 CI runs all 59 tests after this separate PR is opened; final CI evidence will be recorded on the PR.

Tests cover normal confirmation/persistence, positive/negative overlap boundaries, adjacent/cancelled intervals, malformed JSON and invalid inputs/spoofed ownership, stale active/capacity state, retry isolation after the start time, rollback injection, valid/missing/invalid CSRF, different-customer simultaneous booking, simultaneous same-key retry, and the same key racing across different tables. A real register → login → confirm → filtered GET → logout → denied POST scenario exercises Noctowl's merged session flow with CSRF rotation.

The official PostgreSQL binaries cannot run locally because this container maps only uid 0 and PostgreSQL refuses root execution. No privilege workaround was applied. See the PR checks for real PostgreSQL evidence. Source file output in RMS-08-09-local-test-output.txt records the actual combined local run.

## Demo

1. Fresh PostgreSQL development database: follow backend/README.md, migrate, seed_demo, start Django.
2. Use the merged customer registration/login at `/register/` and `/login/`. Seed users intentionally have unusable passwords; do not enable their passwords. For automated tests, force_login supplies a genuine Django session; this is not a login UI implementation.
3. Visit `/book/`, choose a future local date/time and 2 guests. Check availability, select a table, confirm. Show the BK reference and committed interval.
4. Another customer requests that same interval/table: show 409 and nearest alternative. Adjacent 90-minute intervals succeed. Past dates / 0 guests fail.
5. Show `test_simultaneous_different_customers_exactly_one_booking`: two independent DB connections synchronize at a barrier; expected statuses [201,409] and one confirmed row. Show same-key test [200,201] with one reference.
6. Retry a lost-response request with the identical key/payload => same booking. Change payload under that key => 409. Inject retry-metadata failure => zero booking/key rows, then retry succeeds.

Simple explanation: “Search shows tables that look free. When I confirm, the database lets only one request check and reserve a particular table at a time. The next request sees the new reservation and receives another suggested time. A request key makes retries return the original booking instead of reserving twice.”

## Traceability and limits

REQ-1/UT_01/UT_02: RMS-08 tests. REQ-2/UT_03/UT_04 and added race/retry/rollback cases: test_confirmation.py. IT_01 persistence/conflict API coverage is automated; ST_01/ST_02 full login-to-browser flow uses merged RMS-04/05; a real-browser walkthrough remains pending. SV_03/SV_06 booking-specific checks do not complete Noctowl's system-wide issues. ST_10 50-user, restart durability, cross-browser and usability acceptance remain their owners' work. No full-system pass or approved deviation is claimed.

## Review process

RMS-08 and RMS-09 are separate issue-linked PRs. RMS-09 targets the RMS-08 branch until it is merged; then retarget to main. Reviewers must inspect only RMS-09's changes. Issue #12 stays open/In Review until independent teammate review and owner merge. No author approval or merge is performed. The record of earlier browser/connector publishing blockage is superseded by verified Captain-King-2024 browser publishing; no teammate identity is used.
