# Requirement and test traceability

Baseline: main `b171c48` inspected 23 October 2026. Source procedures, source SHA-256 digests, all 29 numbered requirements and 58 unique planned IDs are in [traceability.json](traceability.json). This is a living supplement; the formal source documents have not been silently revised.

Results stay **Not Executed** here until a complete canonical procedure is run. Automated subcases provide partial evidence and are recorded by executable name in run artifacts. A passing subcase never turns an entire ST/SV procedure or requirement green.

| Requirement | Owner / issue | Design | Actual code | Planned cases | State |
|---|---|---|---|---|---|
| REQ-1 | Captain-King-2024 / #11 | SAD 5.1, 6.2, 7.1 | Pending | UT_01, UT_02, IT_01, ST_01, ST_02 | Pending / Not Executed |
| REQ-2 | Captain-King-2024 / #12 | SAD 5.1, 6.2, 7.1 | `backend/booking/models.py` | UT_03, UT_04, IT_01, ST_01, ST_02 | Partial / Not Executed |
| REQ-3 | Captain-King-2024 / #13 | SAD 5.1, 6.2, 7.1 | Pending | UT_05, UT_21, UT_23, ST_09 | Pending / Not Executed |
| REQ-4 | Captain-King-2024 / #14 | SAD 5.1, 6.2, 7.1 | `backend/booking/views.py` | IT_02, IT_03, ST_09 | Partial / Not Executed |
| REQ-5 | prasanna-p2006 / #18 | SAD 6, 7, 9 | `backend/menu/admin.py` | UT_06, UT_07, UT_08, UT_09, IT_04, ST_03 | Partial / Not Executed |
| REQ-6 | prasanna-p2006 / #19 | SAD 6, 7, 9 | Pending | UT_10, IT_04, IT_05, ST_04 | Pending / Not Executed |
| REQ-7 | prasanna-p2006 / #19 | SAD 6, 7, 9 | `backend/menu/models.py` | UT_11, ST_03 | Partial / Not Executed |
| REQ-8 | prasanna-p2006 / #20 | SAD 5.2, 5.4, 7.2 | `backend/orders/models.py` | UT_12, UT_13, UT_16, IT_08, ST_05 | Partial / Not Executed |
| REQ-9 | prasanna-p2006 / #23 | SAD 5.2, 5.4, 7.2 | `backend/orders/models.py` | UT_13, UT_14, ST_05 | Partial / Not Executed |
| REQ-10 | prasanna-p2006 / #24 | SAD 5.2, 5.4, 7.2 | Pending | IT_06, IT_07, ST_05 | Pending / Not Executed |
| REQ-11 | prasanna-p2006 / #22 | SAD 5.2, 5.4, 7.2 | Pending | UT_15, ST_06 | Pending / Not Executed |
| REQ-12 | Noctowl-Abhay / #2 | SAD 4, 5.3 | `backend/accounts/views.py`, `backend/accounts/serializers.py`, `backend/accounts/models.py` | UT_17, UT_18, UT_19, UT_22, IT_10, ST_07 | Partial / Not Executed |
| REQ-13 | Noctowl-Abhay / #3 | SAD 4, 5.3 | `backend/accounts/permissions.py`, `backend/accounts/resources.py` | IT_09, ST_08, SV_03 | Partial / Not Executed |
| REQ-14 | Noctowl-Abhay / #4 | SAD 4, 5.3 | `backend/accounts/middleware.py` | UT_20, SV_10 | Partial / Not Executed |
| PERF-1 | AkulkrishnaMS / #27 | SAD 6, 7, 9 | Pending | ST_10 | Pending / Not Executed |
| PERF-2 | AkulkrishnaMS / #28 | SAD 5.2, 5.4, 7.2 | Pending | IT_07, ST_05 | Pending / Not Executed |
| PERF-3 | AkulkrishnaMS / #27 | SAD 6, 7, 9 | Pending | ST_10 | Pending / Not Executed |
| SEC-1 | Noctowl-Abhay / #2 | SAD 4, 5.3 | `backend/accounts/serializers.py`, `backend/rms_backend/settings.py` | UT_19, SV_01 | Partial / Not Executed |
| SEC-2 | Noctowl-Abhay / #6 | SAD 4, 5.3 | Pending | SV_02 | Pending / Not Executed |
| SEC-3 | Noctowl-Abhay / #3 | SAD 4, 5.3 | `backend/accounts/permissions.py` | IT_09, ST_08, SV_03 | Partial / Not Executed |
| SEC-4 | Noctowl-Abhay / #7 | SAD 4, 5.3 | `backend/accounts/serializers.py`, `backend/accounts/templates/accounts/account.html` | SV_04, SV_05 | Partial / Not Executed |
| SEC-5 | Noctowl-Abhay / #8 | SAD 4, 5.3 | `backend/accounts/views.py`, `backend/accounts/authentication.py` | SV_06 | Partial / Not Executed |
| SEC-6 | Noctowl-Abhay / #5 | SAD 4, 5.3 | Pending | SV_07 | Pending / Not Executed |
| SEC-7 | Noctowl-Abhay / #9 | SAD 4, 5.3 | Pending | SV_08 | Pending / Not Executed |
| SEC-8 | Noctowl-Abhay / #4 | SAD 4, 5.3 | `backend/rms_backend/settings.py`, `backend/accounts/middleware.py` | UT_20, SV_09, SV_10 | Partial / Not Executed |
| QA-1 | Captain-King-2024 / #15 | SAD 6, 7, 9 | Pending | ST_11 | Pending / Not Executed |
| QA-2 | AkulkrishnaMS / #25 | SAD 6, 7, 9 | `backend/accounts/apps.py`, `backend/booking/apps.py`, `backend/menu/apps.py`, `backend/orders/apps.py` | SR_01 | Implemented / Not Executed |
| QA-3 | AkulkrishnaMS / #29 | SAD 6, 7, 9 | `backend/booking/models.py`, `backend/orders/models.py` | ST_12 | Partial / Not Executed |
| QA-4 | Captain-King-2024 / #16 | SAD 6, 7, 9 | Pending | ST_13 | Pending / Not Executed |

## Reconciliation

UT_21, UT_20, IT_07, ST_09, ST_10 and SV_01–SV_10 have additional source variants stored under their existing ID. They are not new tests. DEV-05 retains ST_09 for cancellation/staff workflow and ST_10 for 50-user load. ST_09 retains the original walk-in procedure and revised customer-cancel/rebook scenario as coverage obligations. ST_10 retains both source protocols (5-minute simultaneous start and 10-minute load after a 1-minute ramp); choosing one release protocol requires review. IT_07 uses 20 saved-to-screen samples with at least 19 within one second, while retaining functional display assertions; PENDING-04 still needs approval. UT_20 tests 1799/1800/1801-second boundaries in code while full deployment acceptance remains separate. SV_06 follows DEV-03 (missing identity 401, invalid CSRF 403); its older contradictory wording remains visible.

QA-1 through QA-4 are restored to the matrix from the SRS body and Test Plan section 13. ST_14 is the SRS 6.5 business rule, not a thirtieth numbered requirement. SAD NFT_01–NFT_06 remain distinct design suggestions outside the 58-case count. New harness checks use H_ IDs; no source ID is reassigned.

## Release gate

Test Plan section 5 requires every planned case executed, no critical/high open defects, all security cases passed, PERF-1/2/3 met, complete requirement coverage and all acceptance criteria satisfied. The current build does **not** meet that gate. Mapping coverage is not execution coverage.

Sprint planning is deferred in Project #1 and issue bodies. This work follows AkulkrishnaMS’s requested foundation/integration subset; no dates, teammate assignments or approval records are invented. RMS-02 remains completed through #34. #35 migrations, accounts.User, seed and PostgreSQL workflow are reused. #36 authentication is merged. #38 remains open; #39 merged into #38’s branch, not main. No pending booking code is represented as main implementation.
