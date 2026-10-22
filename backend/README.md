# Database foundation (RMS-03)

Django owns all PostgreSQL models, migrations and writes (DEV-01). Node.js does not migrate or write business data.

## First setup

Use Python 3.12+ and PostgreSQL. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
cd backend
```

Copy `.env.example` to `.env`, supply your own PostgreSQL database/user/password, and create an empty database owned by that user. Do not commit `.env` or database dumps.

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

`createsuperuser` prompts for credentials; none are supplied by this repository. Open `/admin/` with that account. Restaurant Admins may provision Staff/Customer users and maintain table capacity/active state. Staff and Customers cannot use these administration pages. Passwords are hashed by Django's admin forms. Normal customer registration must use `User.objects.create_user()` and explicitly allowlist public fields; the manager rejects role/staff/superuser escalation. The public registration API now uses that manager and an allowlist; see the authentication contract below.

## Demo data and repeatability

`seed_demo` requires `DEBUG=True` and runs atomically. It creates three `rms_demo_*` users with **unusable passwords**, four reserved tables (901–904; capacities 2/4/6/8, including an inactive table), four menu categories including an unavailable dish, confirmed/cancelled bookings and two orders with price snapshots. All identities use `example.invalid`. Demo Admin cannot log in: create your own administrator with the interactive command above.

Run `python manage.py seed_demo` again safely: existing demo records, dates and prices are preserved and no duplicates are inserted. Do not modify the reserved demo users; a changed role or usable password aborts the command. Run seeding serially during local setup, not from application startup or concurrent workers.

## Models and boundaries

- `accounts.User`: inherited Django password handling and username, unique case-insensitive email, optional unique phone, Customer/Staff/Admin role; default public creation is Customer.
- `booking.RestaurantTable`: unique number and positive capacity.
- `booking.Booking`: protected customer/table keys, positive party size, valid time interval/status, timestamps and availability index.
- `menu.MenuItem`: required name, one of four categories, nonnegative decimal price and availability.
- `orders.Order`: protected customer/optional booking, valid lifecycle status, nonnegative total, timestamps and optional report-only payment mode.
- `orders.OrderItem`: protected menu key, positive quantity and nonnegative checkout unit-price snapshot.

Django uses `id` primary keys; API serializers may later expose `user_id`, `booking_id`, etc. Customer/table/menu references are protected from deletion while history exists. Bookings/orders are not exposed for destructive admin CRUD. Normal flows must retain them using statuses. The future booking API must lock the table and check interval overlap/active capacity inside a transaction (RMS-09). The future order API must revalidate availability, calculate totals server-side and commit order/items atomically (RMS-15/16). This schema alone does not implement those flows or their concurrency tests.

## Tests

From `backend/`, run the real PostgreSQL checks against a disposable local database (the test runner creates/destroys a separate `test_<DB_NAME>` database; the local test user needs permission to create it):

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test accounts booking menu orders
```

Fast SQLite model tests are also available:

```bash
python manage.py test accounts booking menu orders --settings=rms_backend.test_settings
```

The SQLite setting uses an in-memory database and a fast password hasher for tests only. Never use it to run the application. PostgreSQL remains the default. See `docs/RMS-03-verification.md` for results and limitations. Existing IT_01/IT_08 cover booking/checkout workflows; foundation tests support them but do not claim those complete workflows pass.

## Reset and existing development databases

`AUTH_USER_MODEL=accounts.User` must be set **before the first migration**. If you previously migrated the empty RMS-02 skeleton with Django's default `auth.User`, do not apply this change blindly to that database. For disposable local development, configure a **new empty database name**, run the migrations and seed command, then create your local admin again. Keep the old database until you have checked that nothing is needed. Existing databases containing real data require a separately reviewed data migration; no automatic destructive reset is included. Preserve all committed migration files.

### Authentication and scoped security

Customer forms are available at `/register/`, `/login/` and `/account/`. The JSON authentication endpoints use Django cookie sessions and CSRF, including public register/login requests. See [the authentication contract and actual test evidence](docs/auth-security-contract.md) for payloads, permissions, the 30-minute idle boundary, teammate integration points and pending cross-module checks. This work reuses `accounts.User` from RMS-03 without changing migrations.
