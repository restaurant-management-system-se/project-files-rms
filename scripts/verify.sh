#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p test-results
python quality/check_traceability.py
(cd backend
 python manage.py check
 python manage.py makemigrations --check --dry-run
 python -m coverage run --branch --source=accounts,booking,menu,orders,auditlog,rms_backend --omit='*/test*.py,*/migrations/*,*/wsgi.py,*/asgi.py' manage.py test accounts booking menu orders quality.test_harness --testrunner=quality.runner.EvidenceRunner --verbosity=2
 python -m coverage report
 python -m coverage xml -o ../test-results/coverage.xml
 python -m coverage json -o ../test-results/coverage.json
)
(cd realtime; npm ci; npm test)
