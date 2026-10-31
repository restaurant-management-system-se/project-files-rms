# RMS-32 / #17 — delivery status and documentation review

Owner: Captain-King-2024. Observed 31 October 2026, before publication of the three remaining Captain PRs. Main revision: `fa71e740ac1117fe57ac1be4c358d19aa2549dd0`. This is a dated audit, not a live dashboard or release sign-off. See [machine-readable issue/PR snapshot](repository-status-2026-10-31.json).

## Captain contribution and demonstration

| Issue / work | Existing separate PR | Observed delivery |
|---|---|---|
| #10 RMS-03 database/demo foundation | #35 | Merged; head is ancestor of main; reused, not recreated |
| #11 RMS-08 availability / alternatives | #38 | Merged; integrated in main |
| #12 RMS-09 atomic booking / retry safety | #39 | Merged into #38 branch and subsequently integrated in main |
| #13 RMS-10 own cancellation / history | #43 | Merged; original head integrated in main |
| #14 RMS-11 staff booking / override history | #44; follow-up #58 | GitHub says merged into #43's feature branch; head is NOT ancestor of main; staff files/migration absent from main |
| #15 RMS-26 responsive booking usability | #55 (draft) | UI/protocol prepared; three first-time human results pending; keep In Review/draft |
| #16 RMS-27 browser/viewport verification | #56 (draft, stacked on #55) | Automated regression/matrix prepared; full six-version and dependent-flow acceptance pending; keep In Review/draft |
| #17 RMS-32 documentation / deviation evidence | This separate PR | README/index/setup/status/deviation reconciliation and source-hash/link checks; independent review and RMS-29 dependency remain |

Explain the booking contribution: availability searches read confirmed occupied intervals; confirmation locks the selected table and checks overlaps again inside a PostgreSQL transaction; a retry key recovers the same committed booking; cancellation changes status and frees the interval without deleting history. RMS-26 improves the presentation around those services rather than rewriting them.

Demo from this main revision: start PostgreSQL and Django, create a local administrator, seed twice, register/login as Customer, open `/book/`, choose tomorrow 19:00 and two guests, check availability and confirm; note the BK reference, open `/my-bookings/`, cancel, then search the same slot. Browse `/menu/`, add an available dish, review `/cart/` and place a takeaway order; record its server-calculated total and Received state. Staff booking and live tracking cannot be demonstrated from main until their owner integrations below are reviewed. New booking UI is reviewed through #15's branch, not silently represented as merged.

## Integration discrepancies requiring owner action

An ancestry check is evidence that a head commit is included, not a guarantee the final code was not later reverted. File/route/workflow inspection corroborates the missing functionality below. Source hashes and exact snapshots make this review reproducible.

| Owner | PR / issue | Observed state and concrete next step |
|---|---|---|
| AkulkrishnaMS | #40 / #30 RMS-29 | Open, head a4296a2; review source reconciliation and canonical RTM. This is an explicit dependency of #17. Do not recreate/edit his RTM here. |
| AkulkrishnaMS | #41 / #31, #42 / #32 | Marked merged into predecessor feature branches; heads 5254e63 / 2a2cebe not in main. `quality/` is absent; main still has the basic foundation workflow. Owner must integrate reviewed stack and rerun on final main. |
| Captain-King-2024 | #44 / #14 | Marked merged into feature/rms-10-customer-cancellation; f1f76c8 absent from main. Preserve existing implementation, review integration of staff files/0003 override migration, rerun PostgreSQL tests and coordinate audit. Follow-up #58 reuses the eleven existing files unchanged and targets main; fresh integration checks/review are required. This is not a second implementation. |
| prasanna-p2006 | #51 / #22 | Marked merged into feature/prasanna-rms-15-checkout; a2c28f7 absent from main. Integrate reviewed stale-cart handling; #22 remains open. |
| Noctowl-Abhay | #46 / #9 | PR open/draft; #9 already closed. Audit service/retention not integrated. Owner should reconcile issue state and obtain independent review/integration; closing issue alone is not SEC-7 evidence. |
| prasanna-p2006 | #52 / #23, #53 / #24 | PRs open; #53 draft while #24 already closed. Staff status/live service not in main. Owner resolves stacked integration and closure mismatch. |
| AkulkrishnaMS | #26, #27, #28, #29 | Reconnect, 50-user performance, websocket latency and restart/rollback acceptance remain open; no completion PRs observed. Historical functional tests do not satisfy these procedures. |
| Noctowl-Abhay / AkulkrishnaMS | #6 / #54 | HTTPS/WSS issue open; production-config PR #54 open. It proposes Gunicorn/WhiteNoise/static/CSRF/health but excludes deployment workflow/host/Node service. Local development and passing CI are not complete CD. |

No teammate branch is edited, no source requirements are waived, and no reviewer identity is impersonated. This documentation does not merge/reopen/close teammate issues. Integration discrepancies are flagged for review; the completed implementations are reused.

## Actual evidence and limits

| Scope / tested head | Recorded execution | What it does not establish |
|---|---|---|
| RMS-03 PR #35, original feature head | [PostgreSQL run 39713040518](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/39713040518): 10 tests passed; fresh migration / seed twice | Later-feature or release acceptance |
| RMS-08 PR #38, original head | [PostgreSQL run 39739686589](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/39739686589): 43/43, no skips | Latest-browser rendering / load / approved nearest policy |
| RMS-09 PR #39, 97012ed | [PostgreSQL run 39740849538](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/39740849538): 59/59; races returned one winner and safe retry | New UI head, human usability or six-browser acceptance |
| RMS-10 PR #43, 23cfe20 | [PostgreSQL run 40630239041](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/40630239041): 71 passed, 1 SQLite-only skipped; cutoff/owner/rollback/races | Main integration of staff feature |
| RMS-11 PR #44, f1f76c8 | [PostgreSQL run 40631152906](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/40631152906): 85 passed, 1 SQLite-only skipped | Inclusion in main or deployed audit acceptance |
| Akul CI stack 2a2cebe, historical main 9b4f49f | [Run 39901326657 attempt 2](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/39901326657/attempts/2): PG 63/63 and Node 3/3 | Current main expanded CI/CD; heads not integrated |
| Live-order stack b5cb6d8 with pinned audit c14d4469 | [Run 40642839500](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/40642839500): feature 79 passed/2 optional-audit skips; combined audit 118 passed/1 SQLite-only skip; Node 2/2 | Current main tracking, deployed WSS, universal one-second delivery, reconnect, all 58 planned procedures |

Historical results above are transcribed from the original issue/PR evidence retained in this session. They are not re-executions on the documentation head and do not imply human review. Fresh documentation/SQLite checks are recorded below and in this PR. Current workflow checks should always be read against their own SHA and run attempt.

No complete security, browser, load, usability, full regression or release pass is claimed. Source Test Plan procedures remain planned unless their own execution records demonstrate all steps. No fabricated reviewer sign-off, human participant, elapsed time, video, backup/restart test or burndown is recorded.

## Documentation/source review

Original [SRS](../../SRS%20and%20Test%20Plan%20Details/SRS/SRS-_Restaurant_Management_System.pdf), [Test Plan](../../SRS%20and%20Test%20Plan%20Details/Test-Plan/Test_Plan_Restaurant_Management_System_SE.pdf), [SAD](../../Software%20Design%20And%20Architecture%20Specification/SAD-%20Restaurant%20Management%20System.pdf) and [additional cases](../../Test%20Cases%20related%20to%20Test%20Plan/Test_Cases-Restaurant_Management_System.pdf) are preserved byte-for-byte in [the hash manifest](source-document-hashes.json). QA-1/ST_11 requires three first-time testers <=3 minutes / <=6 interactions; QA-4/ST_13 requires latest two stable Chrome/Firefox/Edge versions. Preparing scripts does not execute these gates.

[Deviation register](../../Issues/Backlog/DEVIATION_REGISTER.md) retains approved DEV-01–07 and pending semantics (escaping, phone-only registration, order cancellation, latency interpretation, auth envelope, socket-session invalidation, test-ID/source crosswalk). The appended DOC-01–05 record original statement, observed difference, reason/impact, provenance and approval/owner status. No `[cite: N]` source mapping, missing approval minutes or teammate agreement is invented.

Working dates from the user: Sprint 1 19–23 October; Sprint 2 26–31 October 2026. Product Backlog inspection showed 32 items and deferred planning text, with Title/Assignees/Status/Linked PRs/Subissues/Story Points and no formal Sprint field in the inspected view. #15–17 originally remained Backlog/unassigned; completing their deliverables now does not reconstruct a historical sprint. Original sprint outcomes, full-team burndown, working-product videos and release freeze remain unverified.

## Fresh checks on 31 October 2026

- Documentation checker: **16 local links valid, 8 formal source hashes unchanged**.
- This documentation checkout (base fa71e740, no app changes): 93 SQLite tests discovered; **67 passed, 26 PostgreSQL-only skipped**, 1.337s. Django check and whitespace checks passed.
- Separate RMS-26 PR #55 head **621e179970966e3f675072d3e2aa9b3aaaffaf44**: [PostgreSQL run 41184530552](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/41184530552), job 124488603544 succeeded. **93 discovered, 92 passed, 1 SQLite-only skipped, 53.438s**; fresh migrations and repeated seed passed. Log confirms 201/409 same-table race (one confirmed row), safe same-key confirmation, cancel/rebook serialization, one cancellation transition and one checkout order plus retry replay. All five published RMS-26 files match the tested local source tree.
- PR #56 head **f132b25c96534285b200d6069557e6e819817b0a**, checked-out merge **6712141ec84582696929e0e76d0cbe93fa2ee718**: [browser run 41185342546](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/41185342546) succeeded. Chromium job 124491025537: **2 test methods / 6 viewport scenarios passed, 16.245s**; Firefox job 124491025375: **2 methods / 6 scenarios passed, 20.526s**. Bundled Chromium 156.0.8078.4 and patched Firefox 157.0 were installed by Playwright 1.64.1; per-case actual version/SHA/viewport JSON and screenshots are in retained run artifacts. This is twelve scoped scenario executions, not twelve independent first-time testers or the six stable branded-version gate. The same PR head's [PostgreSQL run 41185342561](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/41185342561), job 124491025382: **92 passed / 1 SQLite-only skip, 53.329s**.
- Earlier browser runs 41184789850 / 41184842023 failed on fixture ORM calls made from Playwright's active event-loop thread; 41185035304 failed on exact label punctuation. Fixes use a separate synchronous DB thread with connection cleanup and correct label matching; Django async-safety checks remain enabled. The successful rerun above preserves those failed attempts rather than erasing them.
- Follow-up staff integration PR **#58** reuses original #44 code, with main fa71e740 merged cleanly in an isolated local verification tree. **107 discovered, 72 passed / 35 PostgreSQL-only skipped, 1.389s** locally; Django/migration/JavaScript/diff checks passed. Fresh integration PostgreSQL CI and teammate review are required; no new main delivery is claimed before owner merge.

## Verification commands for this PR

Run from repository root: `python backend/verification/check_documentation.py`. It checks all local Markdown links in the maintained documents and every formal-source SHA256. It performs no network requests or writes. From backend, run the normal Django check and SQLite regression; record their actual results in the PR after execution. No production/app code changes or new migrations belong to #17.

Review gates: Akul reviews RMS-29/traceability and setup/CI status; Noctowl reviews deviation/security wording; another owner reviews and merges this PR. Keep #17 In Review until dependency review and owner merge. The missing human/browser/deployment acceptance remains visible after a documentation merge; updating the index cannot complete those separate issues.
