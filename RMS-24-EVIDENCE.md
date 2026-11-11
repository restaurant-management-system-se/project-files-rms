# RMS-24 / issue #27 — 50-user capacity

| Source | Executable | Executed result |
|---|---|---|
| PERF-1, PERF-3; ST_10 ramp/steady proposal | `orders.test_capacity.CapacityTests` | 50 users; 60s ramp + 600s measured steady load; PASS |

Run: https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/41187891912

Measured steady interval: 29,998 responses; 100% within 2 seconds; nearest-rank p95 32.621656 ms; HTTP 5xx 0%; transport failures 0; unexpected HTTP responses 0. The raw file contains all 31,548 observations, with ramp/steady labels; ramp observations are excluded from acceptance calculations.

Workload is a reproducible closed model: 50 authenticated sessions, each making approximately one request/second. Seeded per-user randomness chooses menu browsing/availability/ordering with weights 50/30/20. Sessions and CSRF tokens are prepared before timing. Every order uses a unique retry key and valid isolated synthetic data. Expected successful HTTP codes are checked, so fast permission/validation errors cannot create a false performance pass.

Initial dataset: 50 customers, 50 tables, one menu item. Environment: PostgreSQL 16 service on GitHub ubuntu-latest runner; Linux 7.0.0-1017-azure x86_64, 4 logical CPUs. Hardware/workload/duration and all raw status codes/times are in RMS-24-capacity.json. This is a CI development-server capacity result, not a production-host or larger-dataset guarantee.

## Reproduce

Install backend requirements and configure PostgreSQL DB_* settings. From backend run `RMS_RUN_LOAD=1 python manage.py test orders.test_capacity --verbosity=2`. Django creates/removes an isolated test database. Default timing is 60-second ramp then 600-second steady load, 50 users. Reports are saved to test-results/RMS-24-capacity.json. The acceptance workflow runs this procedure and uploads JSON even if assertions fail.

The separately proposed five-minute simultaneous-start variant is available using `RMS_LOAD_BURST=1 RMS_RUN_LOAD=1 python manage.py test orders.test_capacity --verbosity=2`; it has not been executed here. Changing RMS_LOAD_SECONDS or RMS_LOAD_RAMP away from the standard duration is explicitly labelled noncanonical/smoke. The issue's proposed ST_10 variant still needs independent agreement; this evidence does not silently amend the Test Plan.

PR #60 is stacked on #53. Cumulative PostgreSQL foundation CI passed too. Independent review, dependency merges, retargeting to main and owner merge remain required. Threshold failures must be investigated and the full scenario rerun before making a pass claim.
