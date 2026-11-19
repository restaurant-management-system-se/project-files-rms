# RMS-28 / issue #29 — durability and rollback

| Source | Executable | Evidence |
|---|---|---|
| QA-3; ST_12, IT_01, IT_08 durability/atomicity aspects | `orders.test_durability.DurabilityTests` | PostgreSQL run 41187985162: 2/2 passed, no skips, 1.164 seconds |

Run: https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/41187985162

The adjacent RMS-28-restart.json contains the complete synthetic booking/order responses before and after both service processes restarted. Django/Node PIDs changed from 2870/2871 to 2906/2907; responses are identical, including booking interval, Confirmed/Received statuses, version, total 4.50, quantity and captured price. PostgreSQL remained running against the same test database throughout. This is a service-restart test, not a claim of host/disk-failure resilience.

RMS-28-rollback.json records successful failure injection before booking retry metadata, order retry metadata, and status event commit. No partial booking/order metadata or order lines survive; failed status mutation retains Received/version 1 and creates no event.

## Reproduce safely

Install backend requirements, run `npm ci` under realtime, configure the normal PostgreSQL DB_* environment, then run `python manage.py test orders.test_durability --verbosity=2` from backend. The Django runner creates an isolated test database. The restart test connects both fresh Django processes to that database and starts real Node processes. It does not flush, reseed, migrate or restart PostgreSQL between snapshots. Child processes are terminated in cleanup; Django removes the test database only after verification. Synthetic data only; no credentials are stored in evidence.

The new acceptance workflow runs this command and uploads reports even on failure. The cumulative database foundation workflow also passed. PR #61 depends on #53. Independent review, dependency merges, retargeting and owner merge remain required. This evidence covers the listed aspects and does not claim full execution of every step of the broader planned test cases.
