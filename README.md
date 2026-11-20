# project-documentation
Central repository for all project documents: SRS, Test Plan, Design Documents, etc.

## Project

**Restaurant Management System** — a web-based application for managing table bookings, food ordering, and menu management for a single restaurant outlet.

- **Backend:** Python (Django REST Framework)
- **Real-time layer:** Node.js (WebSocket / Socket.io) for live order-status updates
- **Author:** Abhay Dubey H (PES1UG24CS551), Dept. of Computer Science and Engineering, PES University

## Project documents

| Document | Editable | PDF |
|---|---|---|
| Software Requirements Specification | [DOCX](SRS%20and%20Test%20Plan%20Details/SRS/SRS-_Restaurant_Management_System.docx) | [PDF](SRS%20and%20Test%20Plan%20Details/SRS/SRS-_Restaurant_Management_System.pdf) |
| Software Architecture and Design | [DOCX](Software%20Design%20And%20Architecture%20Specification/SAD-%20Restaurant%20Management%20System.docx) | [PDF](Software%20Design%20And%20Architecture%20Specification/SAD-%20Restaurant%20Management%20System.pdf) |
| Test Plan | [DOCX](SRS%20and%20Test%20Plan%20Details/Test-Plan/Test_Plan_Restaurant_Management_System_SE.docx) | [PDF](SRS%20and%20Test%20Plan%20Details/Test-Plan/Test_Plan_Restaurant_Management_System_SE.pdf) |
| Test Cases supplement | [DOCX](Test%20Cases%20related%20to%20Test%20Plan/Test_Cases-Restaurant_Management_System.docx) | [PDF](Test%20Cases%20related%20to%20Test%20Plan/Test_Cases-Restaurant_Management_System.pdf) |

The Test Plan records actual results and dispositions for all 58 canonical cases. The Test Cases supplement repeats 15 of those cases. See the [acceptance evidence](docs/ACCEPTANCE.md) and [delivery status](docs/DELIVERY-STATUS.md) for coverage and pending checks.

## SAD Summary

The SAD defines an implementable, real-world design for the Restaurant Management System. It uses Django REST Framework for business logic and database transactions, Node.js and Socket.io for live order-status updates, and a relational database for durable booking and order data.

The design includes safeguards against double booking, unavailable menu items at checkout, unauthorized actions, session expiry, and missed WebSocket updates. The UML component diagram uses proper component notation with provided lollipop interfaces and required socket interfaces for REST API, real-time updates, event publishing, and database access.

## Conventions

- **File naming:** `<Document Type> - <Project Name>.<ext>` (e.g. `SRS - Restaurant Management System.docx`).
- **Revision history:** every document should carry its own Revision History table for tracked changes.
- **Traceability:** requirement IDs introduced in the SRS (`REQ-1` … `REQ-14`) should be reused as-is in the Test Plan and Design Documents so items stay traceable across all three.
- **Format:** `.docx` for formal deliverables; `.md` acceptable for lighter-weight or working documents.

## Local Setup Instructions

### Backend (Django)
1. `cd backend`
2. Create a virtual environment with `python -m venv venv`, then activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in your PostgreSQL credentials.
5. Run `python manage.py migrate`, then `python manage.py seed_demo` for development data.
6. Create your own administrator: `python manage.py createsuperuser`.
7. Run server: `python manage.py runserver`.

See [backend database setup](backend/README.md) for model details, safe demo data, tests and existing-database guidance.

### Real-time Service (Node.js)
1. `cd realtime`
2. Install dependencies: `npm install`
3. Copy `.env.example` to `.env`.
4. Run server: `npm start`

## Booking feature work

The public `/book/` search and `/api/tables/availability` endpoint are described in [RMS-08 contract/evidence](backend/docs/RMS-08-contract-and-evidence.md). The implementation reuses the merged RMS-03 migrations/data. Sprint allocation remains pending; integration contracts require teammate review.

Transactional Customer confirmation, retry safety, PostgreSQL concurrency tests and demonstration steps are recorded in [RMS-09](backend/docs/RMS-09-contract-and-evidence.md). Keep linked issues In Review pending teammate review and owner merge.

## Integrated evaluation closeout

The closeout branch integrates the original audit, ordering, realtime, recovery, performance and deployment contributions without changing their authorship. See [delivery status](docs/DELIVERY-STATUS.md), [deployment](deploy/README.md), [acceptance disposition](docs/ACCEPTANCE.md), and [recording checklist](docs/demo/README.md). Source specifications carry a dated reconciliation appendix. Review and owner merge remain required.

Run Python 3.12 with backend/requirements-test.txt, Node 22 and a disposable PostgreSQL 16 database with CREATEDB privileges, then scripts/verify.sh. Optional browser, capacity and render-latency acceptance suites have separate workflows and must retain their actual outputs.
