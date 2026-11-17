# RMS-11 staff bookings — issue #14

Owner Captain-King-2024; Sprint 2 **26–31 October 2026**, work performed from 28 October. Separate PR stacked on RMS-10 (#13); retarget to main after its reviewed owner merge. Keep #14 open/In Review until independent review/owner merge.

## Boundaries and API

Reuse RMS-03 tables/users/bookings, RMS-04/05/06 cookie sessions and CSRF, RMS-08 availability, RMS-09 confirmation and RMS-10 cancellation. No account fields, existing entity fields, auth source, existing API behavior, or teammate CI files change. `create_locked_booking` extracts the existing table checks without changing customer confirmation semantics; both callers lock their customer and then the selected table. Regression tests cover the unchanged customer flow.

- `GET /api/staff/bookings`: Staff/Admin only. `q` searches BK-reference/ID, customer email/name/username or table number; `date=YYYY-MM-DD` filters UTC start date; `status=Confirmed|Cancelled`; page>=1, 25 rows, total/page counts. Invalid filters return 400; blank date/status mean all. Existing customer GET /api/bookings stays owned.
- `POST /api/staff/bookings`: existing active Customer `customer_id`, `table_id`, timezone-aware `start_at`, positive integer `party_size`, actor-scoped `idempotency_key`, required `reason` up to 500 characters. Same duration, active/capacity/future/half-open overlap checks as customer creation. 201 after commit; identical retry 200; changed payload/key 409. Conflict includes fresh availability/nearest alternatives. Walk-ins use an existing/newly registered Customer account; anonymous booking requires a separately agreed model change and is not invented here.
- `POST /api/staff/bookings/{id}/cancel`: required reason only; any booking. DEV-02 permits Staff/Admin cutoff override, retaining the booking. Already cancelled returns 200/changed=false without duplicating evidence. Missing record 404. No booking delete/update endpoint is added; DELETE is denied.
- `/staff/bookings/`: protected responsive dashboard, filters, manual form, cancellation reasons, pagination and escaped actor/reason history. Cookie session, idle expiry, logout and CSRF reuse Noctowl's existing boundary. Customers receive 403; anonymous callers 401.

## Atomicity and evidence

All writes require PostgreSQL (503 otherwise). Staff actor row is locked first, active role rechecked, then Customer row, table, booking when applicable. Staff actors cannot be target Customers. This extends the customer→table lock order without changing it. Different customers/staff targeting one table serialize on the same row. Cancel/create transactions return only after durable commit.

Additive migration 0003 creates **BookingOverride**, a booking-owned record containing protected actor/booking references, Create/Cancel action, reason, timestamp and actor-scoped retry payload/key. Mutation and evidence commit together; injected evidence failures roll back the booking/status. No mutation/admin/delete API exposes these records. No cleanup is added, so evidence is retained indefinitely. This satisfies recording for this booking feature; the wider privileged-action audit/retention policy remains Noctowl's RMS-23, including cross-feature centralization and operational retention controls. No approved shared audit contract is claimed; review the additive boundary before merge.

## Verification and demonstration

Local full suite: 86 discovered, 56 passed, 30 PostgreSQL-only tests skipped, 1.218s. Migration consistency and JavaScript syntax checks passed. Prior failed local request-shape test exposed a serializer error-envelope bug, corrected to a dictionary ValidationError and rerun successfully. PostgreSQL CI must execute both features before acceptance; exact run/revision/results are recorded in the PR conversation after execution, not predicted here.

New tests cover Staff/Admin vs Customer/anonymous, CSRF/logout, payload/search/date/status validation, retained history/output escaping, pagination, cutoff override, customer-cancel→staff-rebook, walk-in creation, unchanged customer confirmation, capacity/active/overlap/adjacency, safe retries, evidence failure rollback, and three staff/customer races. Existing RMS-09 and RMS-10 races remain in the full suite. Mapped procedures: IT_02, IT_03, ST_09, ST_14, SV_03; these are automated subcase evidence, not a claim that every full manual procedure was executed.

Demo on PostgreSQL: migrate/seed; Admin provisions a Staff account; customer registers and books. Staff logs in at /login/, opens /staff/bookings/, searches by BK-reference/date/status, creates a booking for a registered walk-in with reason, cancels inside the 30-minute window with reason, and rebooks the freed slot. Verify actor/reason/time in history and that the cancelled record remains. Customer cannot enter staff dashboard or staff API. Human usability/browser/version/load acceptance remains separate.

CI/CD ownership is unchanged: merged database PR workflow is reused. Akul's PR #42 is not merged here, and no deployment target/configuration is invented.
