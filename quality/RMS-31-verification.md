# Sprint foundation and integration evidence

Recorded 23 October 2026. Canonical inventory counts and executable counts are different: the 58 planned procedures are preserved with their complete acceptance scope; a runtime test count does not imply 58-case acceptance.

| Build / source | Environment | Actual result | Limits |
|---|---|---|---|
| Main b171c48 + RMS-29 documentation | Python 3.12.14, Django 6.1.2, fresh SQLite | 35 existing tests passed; checks clean | No PostgreSQL concurrency claim |
| RMS-30 local working tree, recorded in RMS-30-local-evidence.json | Same pinned Python dependencies, fresh SQLite | 39 passed, 0 skipped, 1.066 s; SR_01 and reporter/role/clock support included | Evidence explicitly records dirty source state; committed-upload verification and CI are separate |
| RMS-30 Node client fixture | Fresh npm ci, Node 24.19.0 | 3 passed, 0 skipped, about 0.216 s | Synthetic loopback fixture, not production WebSocket/security/latency acceptance |
| Disposable integration branch: 19a7a3e + candidate a9edf226 | Fresh SQLite with candidate migrations | 63 discovered, 51 passed, 12 PostgreSQL-only skipped; 1.131 s; no model drift, system checks clean | README conflict resolved only in the disposable checkout; no feature-owner source or branch changed; not main delivery |
| Existing owner run 39753262527 / PR #38 merge test 0355def1747149446f01076f4d21634fdd413878 | GitHub Actions, PostgreSQL 16.15 | 59 passed, no skips, 29.028 s; fresh migrations/two seed runs; real registration-booking-logout flow and all 3 races passed | Owner's existing run inspected; it does not include Akul's 4 new harness tests |

The owner run is [39753262527](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/39753262527), job [119738807961](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/39753262527/job/119738807961). Its raw logs were inspected for test count, success, PostgreSQL version and each concurrency case. This is reused evidence, not a claim that Akul executed a new 63-case PostgreSQL integration run.

Published harness head `5254e6328ff98236b5188839e2cf46d75e164953` was fetched into a separate clean checkout. All 14 changed files byte-matched the tested source. Fresh setup reran RTM validation, 39 Django tests (1.045 s), fresh npm ci and 3 Node tests (0.224 s): all passed; working tree clean. Existing PostgreSQL CI [39899355920](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/39899355920), job 120237068790, passed 35 existing tests on PostgreSQL 16.15 in 13.824 s. This old workflow does not select the 4 new harness checks; the RMS-31 extension will run all 39 and Node checks. Its result is Pending until actually executed.

## Current blockers and next owners

- #38 is still open; #39 merged into its feature branch, not main. Captain owns review/merge and feature fixes. Candidate test evidence is kept distinct from main.
- Prasanna owns missing menu listing/grouping, cart, atomic checkout, stale-item rejection, status lifecycle and authorized realtime delivery (#18–24). No menu → cart → order → live tracking pass is claimed.
- Noctowl/feature owners retain lockout, deployment TLS/WSS, audit and cross-module security work. Deployed browser/TLS/session/socket acceptance remains pending.
- PENDING-01–07 in the deviation register need team decisions; a proposed contract is not an approval. Source documents are not silently revised.
- Performance, usability, restart, and six browser/version acceptance checks remain pending. Local smoke timing is not PERF-1/2/3 evidence.
- This local container maps only uid 0 and lacks a PostgreSQL service; Actions is the actual PostgreSQL execution environment. SQLite-only confirmation/race skips are reported as skips.

The Test Plan release gate remains unmet. Keep unexecuted canonical procedures pending, all three issues In Review, and require independent teammate review and owner merge.

## Updated main observed during final verification

PR #38 is now merged into main `9b4f49f80152e2f2fe1395c89a1abd74e49b1854`, including #39. Earlier open/candidate statements above describe their recorded baseline and are superseded for the current repository. No human review submission was returned for #38; merge is observed, independent review is not invented. REQ-1 now maps to `backend/booking/availability.py`, `serializers.py`, `tests.py` and the booking page; REQ-2 maps to `backend/booking/services.py`, `request_models.py`, migration 0002 and `test_confirmation.py`. Availability/confirmation are implemented on main; performance/full browser acceptance remain pending. The external executable map now includes all 24 booking tests with scoped requirement/case support.

The initial RMS-31 CI run [39899949518](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/39899949518) passed PostgreSQL and Node jobs. The follow-up prepares current main in the disposable PostgreSQL job to test all 63 Django executables together; its outcome remains Pending until run. No production source from the booking owner is rewritten or pushed by Akul.

## Combined PostgreSQL execution completed

Run [39900859010](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/39900859010) passed at PR head 7880883c5eb8bb492f614414b1356fd2d52d8b00. The runner checked out PR merge revision 848cc3d432109ebbfa5d23c39c3c46df657795bc, integrated main 9b4f49f, and tested index tree 481979204c38e9858827478fb45abe6927a2b846 (same tree as local preparation). Python 3.12.15, Django 6.1.2, PostgreSQL 16.15: **63 passed, 0 skipped, 16.985 seconds**. Node 22 fixture JUnit contains **3 passed, 0 failed/skipped**. Job logs, raw Django JSON and Node JUnit were inspected.

The unmodified artifact records are preserved as RMS-31-postgres-execution.json and RMS-31-node-execution.xml. GitHub artifact IDs 12478951869 and 12478508251 retain full logs/environment until 22 November 2026. The PostgreSQL job also passed fresh migration, repeated seed and RTM checks. The README reminder check passed; its paginated marker upsert retained one reminder.

The canonical RTM is now updated to main 9b4f49f for actual booking paths and its complete SR_01 static result. Exactly 1 of 58 complete canonical procedures is marked Passed; 57 remain Not Executed, despite many passing automated subcases. REQ-1/2 acceptance remains partial where browser/performance scope is unexecuted. This supersedes the earlier Pending outcome. Menu/cart/checkout/status/production sockets and all release-level blockers above still apply.
