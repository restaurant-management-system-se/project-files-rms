# RMS backend coverage — 19 November 2026

Source: restaurant-management-system-se/project-files-rms, main commit 8c1cf479ec5ced7c68c1f8641594b226557be390.

Executed: 107 tests; 72 passed; 35 skipped; zero failures.
Database: SQLite in-memory, rms_backend.test_settings.
Coverage.py: 7.17.3, branch measurement enabled.

- Statement coverage: 84.47% (952 / 1127 statements).
- Branch coverage: 62.16% (138 / 222 branches).
- Combined coverage: 80.80% (coverage.py rounds to 81%).

Open html/index.html for file-by-file coverage and uncovered lines.
coverage.xml supports CI tools; coverage.json has exact totals.
test-output.txt is actual run output.

Scope: accounts, booking, menu, orders and rms_backend Python code. Excludes test files, migrations, WSGI and ASGI entry points. This is not JavaScript, browser UI, full repository, PostgreSQL concurrency or full Test Plan coverage. PostgreSQL-only tests were skipped, which lowers service-path coverage. No tests were disabled or rewritten to inflate results.

Reproduce from backend after installing backend/requirements.txt and coverage==7.17.3:

python -m coverage run --branch --source=accounts,booking,menu,orders,rms_backend --omit='*/test*.py,*/migrations/*,*/wsgi.py,*/asgi.py' manage.py test accounts booking menu orders --settings=rms_backend.test_settings --verbosity=1
python -m coverage report -m
python -m coverage html
python -m coverage xml

For PostgreSQL, configure a disposable database with CREATEDB permission and omit --settings=rms_backend.test_settings. Generate a separate report and retain its actual skipped/failure counts.
