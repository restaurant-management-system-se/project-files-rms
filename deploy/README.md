# Deploy RMS on a local or hosted Linux machine

The deployment target must have PostgreSQL 16+, Python 3.12, Node 22+ and Caddy. Local development uses Django's development server; deployment uses Gunicorn. No host, certificate issuance or public service is provisioned by committing these files.

1. Check out the reviewed release commit; create a virtual environment. Install backend/requirements.txt and run npm ci in realtime/.
2. Create a PostgreSQL database and restricted application login. Apply migrations using a controlled deployment login; keep the application database and backups persistent across releases.
3. Copy backend/.env.example to backend/.env and realtime/.env.example to realtime/.env. Set a private Django SECRET_KEY and a separate random RMS_REALTIME_KEY of at least 32 characters. The latter must match in both services. Never commit the values.
4. For a public deployment set DEBUG=False, ALLOWED_HOSTS to the hostname, CSRF_TRUSTED_ORIGINS to its HTTPS origin, RMS_PUBLIC_ORIGIN to that same origin and RMS_PUBLIC_HOST for Caddy. Bind Django, Node and PostgreSQL to loopback/private interfaces only.
5. From backend/: python manage.py migrate --noinput; python manage.py collectstatic --noinput; python manage.py check --deploy. Create the first administrator with createsuperuser. seed_demo is for disposable demonstration environments, not customer data.
6. Start from backend/: gunicorn rms_backend.wsgi:application --bind 127.0.0.1:8000. From realtime/: npm start. Have a process supervisor restart each service and the outbox publisher: python manage.py publish_order_events. See that command's --help for the available invocation; schedule retries through the supervisor or a timer.
7. Run Caddy using deploy/Caddyfile. It terminates HTTPS/WSS, redirects HTTP and rejects public /internal and /api/internal paths. Caddy requires a reachable domain and certificate setup for public TLS. Local development HTTP does not satisfy SEC-2 or secure-cookie acceptance.
8. Visit /health/, then rehearse sign-in, booking, checkout and tracking. Verify HTTP redirect, TLS 1.2/1.3, Secure/HttpOnly cookies, blocked internal URLs and session expiry before signing SV_02/SV_09.
9. Schedule python manage.py audit_maintenance through a trusted operator; it retains at least 90 days and reports maintenance actions. Back up PostgreSQL and rehearse restoration. Never run tests against the application database: Django must create its own disposable test database.

## Release and rollback

CI validates the proposed tree. A repository owner approves its PR and records the tested release SHA before deployment. Back up before migrations, install a release in a separate directory, apply compatible migrations, switch the supervised processes, and verify /health/ and the core flow. Roll back application code only after checking migration compatibility; otherwise restore the tested backup according to the maintenance window. CI completion alone is not evidence that deployment occurred.

## Delivery pipeline

The manually triggered RMS reviewed release package workflow runs PostgreSQL regression, traceability and Node checks before producing an exact git archive, revision file and SHA-256 checksum. This is a tested delivery artifact. The operator deploys it using the procedure above; there is no configured deployment host or unattended CD claim.
