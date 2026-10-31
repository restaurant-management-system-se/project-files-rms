# RMS-26 / #15 — booking usability

Owner: Captain-King-2024. Proposed for Sprint 2 (26–31 October 2026) under the user's completion request; the Project still has no formal Sprint field and the issue originally said unassigned. This does not retrospectively approve a whole-team sprint allocation.

## Implemented

The existing RMS-08/09/10 booking services, PostgreSQL transactions and authentication are reused. Only booking templates and client behaviour change. No shared model, migration, auth endpoint or teammate feature is changed.

The booking page explains the three steps, shows the selected interval before confirmation, uses connected inline errors, announces pending requests and focuses the confirmation. Inputs/results fit narrow screens, controls have a minimum 44px height and keyboard focus is visible. All confirmation controls are disabled together while a request is pending. Changing search input invalidates old results; a late failed search cannot overwrite a newer successful search. A network retry retains the same request key. Confirmation links directly to cancellation/history. Dates are displayed in the device's timezone. Server validation remains authoritative.

## ST_11 neutral human protocol — acceptance still pending

Recruit three people who have never used RMS. Do not show them the interface beforehand or coach them. Use pseudonyms T1–T3; do not commit names, credentials, recordings or personal information. Obtain permission before recording anyone.

Starting state: a fresh browser context on `/book/`, already authenticated as a fresh test Customer, with an active table of capacity >=2 free tomorrow at 19:00. Reset the fixture to an equivalent free-table state between participants; use distinct customers, not a reset of real data. Record browser/version, viewport, timezone, build SHA and fixture ID. Registration/login are separate functional tests; their exclusion from the timed task follows the existing-account precondition and is an explicit protocol choice for reviewer approval.

Read exactly: **“Book a table for two guests tomorrow at 19:00. Tell me when you think your booking is confirmed.”** Start the stopwatch after reading this and giving control of the page. Stop when the participant recognizes the visible booking reference and correct visit details. If asked for help, say “Please do what you would normally do”; record any intervention and do not count an assisted run as a pass.

Interaction rule, fixed before testing: one field edit (including all keystrokes/date-picker actions needed to complete that field), one button/link activation or one page navigation is one interaction. Corrections/repeated activations count again. Reading, pointer movement, focus-only Tab navigation and passive scrolling do not count. Keep the ordered action log so another reviewer can recompute the count. This is a proposed operational definition; obtain independent review before treating it as the approved measurement method.

Each participant must finish in <=180 seconds and <=6 interactions, without assistance. All three must pass independently. A bot, scripted browser duration or developer walkthrough cannot substitute for a first-time participant. Record failures and retain them. After a material fix, use new first-time participants or clearly mark the retest as learned/assisted and obtain an agreed fresh-test design.

| Tester | Fixture/build/browser/viewport | Ordered actions | Seconds | Interactions | Assistance/defect | Outcome |
|---|---|---|---|---|---|---|
| T1 | Not executed | — | — | — | — | Not executed |
| T2 | Not executed | — | — | — | — | Not executed |
| T3 | Not executed | — | — | — | — | Not executed |

Also inspect 320x568, 390x844 and 1280x800, keyboard-only submission, invalid/past dates, zero/fractional guests, no-table alternatives, conflict response and network retry. Record observed browser results separately from ST_11 human measurements.

## Review and execution

Use `python manage.py test accounts booking menu orders` against PostgreSQL, plus `node --check booking/static/booking/book.js` from `backend/`. SQLite is a regression smoke only, never booking concurrency evidence. Browser regression automation is maintained separately under RMS-27 (#16). Actual run results are added to the PR and companion evidence file after execution.

Keep #15 open / In Review and its PR draft until three qualifying human results and independent review are available. No usability pass, product video or release freeze is claimed here.
