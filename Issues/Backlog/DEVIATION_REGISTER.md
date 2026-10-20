# Deviation and Conflict Register — Restaurant Management System (RMS)

This register tracks identified ambiguities, terminology variations, or minor conflicts across the Software Requirements Specification (SRS), Software Architecture and Design Specification (SAD), Test Plan, and Test Case documents, providing a single agreed baseline for implementation and evaluation.

## Summary Table of Resolved Deviations

| Conflict ID | Area / Topic | Affected Documents | Description of Conflict | Approved Resolution / Baseline Rule | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEV-01** | Node.js Database Ownership | SAD, SRS, Test Plan | Ambiguity regarding whether Node.js communicates directly with PostgreSQL or via Django. | Node.js **never** writes directly to the database or owns business rules[cite: 9, 11]. Django processes transactions and commits state changes first, then triggers an internal event to Node.js for WebSocket push delivery (`realtime/server.js`)[cite: 9, 11]. | **Approved**[cite: 62] |
| **DEV-02** | Order Cancellation & Staff Policy | SRS, Test Plan, Test Cases | Customer cancellation is strictly time-bound (up to 30 minutes before reservation)[cite: 58], while staff override allows manual cancellations/modifications[cite: 12, 58]. | Customers can cancel up to 30 minutes prior[cite: 58]. Staff/Admins can manually override or cancel any booking from the dashboard, which must be fully recorded with an audit trail and reason[cite: 12, 58]. | **Approved**[cite: 62] |
| **DEV-03** | 401 Unauthorized vs. 403 Forbidden | SRS, SAD, Test Plan | Inconsistent error codes mentioned for unauthenticated requests vs. unauthorized roles across specifications. | **401 Unauthorized** is strictly returned when authentication tokens/credentials are missing or invalid[cite: 15, 57]. **403 Forbidden** is returned when an authenticated user lacks the required role permissions (e.g., Customer accessing Admin endpoints)[cite: 15, 57]. | **Approved**[cite: 62] |
| **DEV-04** | Public Endpoints & Authentication | SRS, Test Plan | Definition of which read APIs are fully public vs. authenticated. | Menu viewing (`/api/menu`) and table availability searches (`/api/tables/availability`) are public; all management, booking actions, and cart/orders require authentication[cite: 20]. | **Approved**[cite: 62] |
| **DEV-05** | Test ID Duplication (`ST_09` / `ST_10`) | Test Plan, Test Case Document | Overlapping test identifier usage for table cancellation vs. performance load testing. | Reconciled duplicate identifiers; retained canonical unique IDs (`ST_09` for customer cancellation/staff dashboard workflow, `ST_10` for 50-user performance load testing)[cite: 2, 4, 37]. | **Approved**[cite: 62] |
| **DEV-06** | Payment Mode Field Scope | SRS, Test Plan | "Payment Mode" appears in the Order Report schema without payment gateway integration. | Maintained "Payment Mode" purely as a static/optional reporting data field in the data schema to satisfy report requirements, confirming actual payment processing is **out of scope** for Version 1.0[cite: 32, 59]. | **Approved**[cite: 32, 59, 62] |
| **DEV-07** | Sprint Dates and Allocations | Test Plan, Project Management | Initial draft schedules and author names left as placeholders. | Kept sprint dates, timeline tracking details, and resource team name allocations **unset/flexible** to align with academic mini-project structures[cite: 38, 62]. | **Approved**[cite: 38, 62] |

## Detailed Notes on Key Governance Decisions

### 1. Data Flow Integrity (DEV-01)
* **Architectural Rule:** The PostgreSQL database is exclusively owned by Django via the ORM layer[cite: 9, 10, 11]. Node.js serves solely as a real-time messaging layer utilizing Socket.io for dispatching order-status changes over secure WebSockets (WSS) to authorized client rooms[cite: 9, 10, 11, 28].

### 2. Security and Access Control Enforcement (DEV-03, DEV-04)
* **API Boundary Rule:** Every state-changing API endpoint (`POST`, `PUT`, `PATCH`, `DELETE`) enforces rigorous CSRF checks (for session cookies) and Bearer/Token validation[cite: 13, 57]. Unauthorized escalation attempts are instantly logged and rejected with appropriate HTTP status codes (`401` or `403`)[cite: 15, 57].
