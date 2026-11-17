# RMS-10 customer cancellation — issue #13

Sprint 2: **26–31 October 2026**, supplied by Anku. Work started 28 October; no earlier execution is claimed. Owner: Captain-King-2024. Separate PR; leave the issue In Review until independent teammate review and owner merge.

## Contract

- Reuse merged RMS-03 (#35), authentication (#36), booking (#38/#39). Existing entity fields, migrations, authentication sources and customer confirmation/read contracts stay unchanged.
- `POST /api/bookings/{id}/cancel`, empty JSON object, authenticated customer session and valid CSRF token. Server derives owner. Unknown fields/non-object bodies: 400. Anonymous: 401. Wrong role/CSRF: 403. Missing or foreign booking: 404. Cutoff: 409. DELETE remains forbidden by the shared permission.
- PostgreSQL required for mutations (503 on SQLite). A durable transaction locks customer→table→booking, following RMS-09's lock order. Revalidate the locked user. Evaluate timezone-aware server time after locking: exactly 30 minutes is allowed, any smaller interval is denied.
- Update status/updated_at and commit before returning `{id, booking_id, status, changed}`. Retain Booking and request key. Repeated cancellation returns 200/changed=false even after cutoff. Rollback retains original status. Confirmed-only availability releases cancelled intervals.
- `/my-bookings/`: owned customer history, 25 per page, newest start first, retained cancellations, device-local times, CSRF-protected action, status/errors and safe network-failure retry. `/book/` links to it.
- Staff overrides belong to RMS-11. General audit/90-day retention remains Noctowl's RMS-23. Neither is implemented in this PR.

The additive contract was posted on #13 for Noctowl/Akul review. A posted proposal is not teammate agreement. Shared models/authentication are not changed. Staff actions must follow the same lock order.

## Verification

New `booking.test_cancellation` checks exact cutoff ±1 second, ownership, invalid payload/methods, CSRF/logout, pagination, retained history/slot release/rebooking, rollback, inactive-user revalidation and real PostgreSQL races. Double cancellation: two 200 responses, one transition. Cancel/rebook: initial 201 or 409 according to table lock order; retry finishes with one Confirmed plus one retained Cancelled row.

```sh
python manage.py test accounts booking menu orders --settings=rms_backend.test_settings --verbosity=2
python manage.py check --settings=rms_backend.test_settings
python manage.py makemigrations --check --dry-run --settings=rms_backend.test_settings
```

The existing PR workflow uses PostgreSQL 16, fresh migrations, seed twice and the complete suite. Record its exact revision/run/counts in the PR after execution. SQLite does not prove concurrency. Human usability, supported browsers, 50-user load, deployment and full ST_09 staff workflow remain pending.

## Demo

1. Configure PostgreSQL using backend/README.md, migrate/seed, register/login.
2. Confirm a table at `/book/` at least 30 minutes ahead. Open **My bookings and cancellations**.
3. Cancel: history displays Cancelled. Search the same interval; the table is free.
4. Cancellation less than 30 minutes before start is denied without changing status. Another customer cannot cancel your booking.
5. Automated PostgreSQL tests demonstrate the exact cutoff and simultaneous requests.

## CI/CD at Sprint 2 start

Merged `.github/workflows/rms-database-tests.yml` runs PostgreSQL checks on backend PRs/main pushes. Akul's expanded PostgreSQL/Node CI is still open in PR #42, stacked on #41/#40; latest run 39901326657 succeeded. Independent review and owner merge remain pending. No deployment workflow/target was found. Full CI/CD is not complete; RMS-31 (#32) remains Akul's issue.
