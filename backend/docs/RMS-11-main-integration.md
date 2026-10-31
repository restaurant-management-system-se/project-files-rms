# RMS-11 / #14 — integrate the existing implementation into main

31 October 2026. Owner Captain-King-2024. Original implementation PR #44 was merged into `feature/rms-10-customer-cancellation` at 6d98a06, rather than reaching main. Its head f1f76c8 and eleven staff feature files are absent from main fa71e740. This follow-up reuses that exact existing code; no competing implementation, entity rewrite or new API contract is introduced.

The focused integration PR targets **main** from a branch starting at 6d98a06, with this evidence note added. The functional diff is the original eleven RMS-11 files: protected staff search/manual creation/cancellation, booking-owned override migration 0003, reused capacity/overlap/retry checks and original tests/docs. Captain remains owner; Noctowl's authentication and proposed audit adapter remain unchanged. General audit service/retention still belongs to #9/#46.

## Actual local verification

An isolated worktree at 6d98a06 was merged with main fa71e740 using `git merge --no-commit --no-ff origin/main`; the merge was clean. The existing tests were executed on that combined tree, not on an out-of-date staff branch.

`python backend/manage.py test accounts booking menu orders --settings=rms_backend.test_settings --verbosity=1`: **107 discovered, 72 passed, 35 PostgreSQL-only skipped, 1.389s**. Django check, migration consistency and JavaScript syntax are checked separately. No local PostgreSQL/concurrency pass is claimed. The previous #44 PG run 40631152906 (85 passed/1 SQLite-only skip) belongs to the old feature head; the new integration must pass fresh PostgreSQL CI before owner merge.

The PR's default GitHub checkout tests the proposed merge with main. Record its exact head/merge/run and outcome in the PR/issue after completion. Do not reuse the old green check as approval of the integrated tree.

## Demo and ownership/review gate

After independent review and owner merge into main: Admin provisions Staff and a Customer; Staff logs in at `/login/` and opens `/staff/bookings/`. Search by BK reference/date/status, create a future booking for the existing Customer with a reason, retry safely, cancel with a reason (including a cutoff override), and verify retained BookingOverride history. A Customer cancellation followed by staff rebooking should release/reuse the interval. Confirm Customer access is forbidden and confirmed history cannot be deleted.

Keep #14 In Review while this integration is reviewed; existing issue closure/PR #44 merge did not establish main delivery. Do not self-approve, merge into another feature branch, or mark deployed audit/human/browser acceptance complete. PR #55's responsive Customer UI and #56's browser verification remain separate issues and do not need to be bundled into this integration.
