# RMS-08 availability: proposed integration contract and evidence

Working scope: Captain-King-2024's proposed Sprint 1 RMS-03/08/09. Project #1 has no formal sprint allocation; issue bodies and DEV-07 explicitly defer planning. No sprint dates or teammates' ownership changed.

Reuse: PR #35 is merged (22 Oct 2026) and PostgreSQL check `postgres` passed at head 30646f7 (run 39713040518). GitHub returned no review submissions; merge actor was Captain-King-2024. Issue #10's review-pending wording is stale. No database foundation was recreated.

Integration proposal posted in #11 to Noctowl-Abhay (RMS-04/05 owner) and AkulkrishnaMS (RMS-02 author/owner). **Acknowledgement pending; not an agreed shared contract.** Existing User/Table/Booking fields and teammate modules are unchanged. URL inclusion/configuration are additive proposal changes for review, not changes to their implementations. Standard Django request.user/session integration is expected; login/registration remain RMS-04. PR must not be merged until contract review.

## API

`GET /api/tables/availability?start_at=2026-11-01T19%3A00%3A00%2B05%3A30&party_size=2` is public per DEV-04. Encode `+` in offsets as `%2B`. ISO-8601 timezone offset is mandatory; party size is an integer 1–32767. Start must be in the future. Invalid input returns 400 `{code,message,details}`. JSON contains start_at/end_at/party_size/tables/alternative. Table objects contain table_id/table_number/capacity. No customer/booking identities are public.

Intervals are half-open `[start,end)`; confirmed bookings alone block, adjacent intervals are free. Inactive or insufficient-capacity tables are excluded. `BOOKING_DURATION_MINUTES` config defaults to 90, allowed 1–1440. Search and confirmation share this duration. `/book/` supplies local-device date/time input and inline errors.

Nearest means smallest absolute distance from requested start across exact free gaps on eligible tables, excluding past starts. Equal distance: earlier start, then smaller sufficient capacity, then table number. Busy intervals are merged by advancing a cursor; each free gap yields its closest feasible start. No sampling grid or finite horizon can miss an interval. No eligible table => alternative null. There is no opening-hours policy in the baseline; this is a pending policy clarification, not an invented business restriction. Availability is advisory and does not lock/reserve a table.

## Evidence (22 Oct 2026)

Python 3.12.14; Django 6.1.2 and pinned requirements. Command from repository root:

`../rms-venv/bin/python backend/manage.py test accounts booking menu orders --settings=rms_backend.test_settings --verbosity=2`

18/18 tests passed, 0.136s test execution; API+template smoke measured 0.0063s. Eight availability tests cover UT_01/UT_02 filtering/input boundaries, cancelled/adjacent intervals, duration, nearest ties, merged busy periods and cross-day alternatives. Ten foundation tests remain passing. SQLite results are functional evidence only. This smoke is neither full browser rendering nor ST_10/50-user performance evidence. IT_01/ST_01/ST_02 complete confirmation/browser integration awaits RMS-09 and auth integration.

See tests in booking/tests.py; PostgreSQL CI runs the same suite through the existing workflow without taking ownership of RMS-30/31.

## Current integration (22 Oct 2026)

Rebased on main b171c48 after Noctowl PR #36 and governance PR #37 merged. The owner-published cookie-session contract in #2 is reused; existing BookingReadView, GET routes and shared auth files are preserved. Booking-owned URL inclusion and duration configuration are additive. No competing user model or authentication implementation is introduced. Nearest-slot/opening-hours policy still needs teammate review.

Latest main integration check: 43/43 SQLite tests passed (35 merged authentication/foundation + 8 availability), test time 1.041s. PostgreSQL CI must also pass. This does not claim browser-render or 50-user acceptance.
