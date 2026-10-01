# project-documentation
Central repository for all project documents: SRS, Test Plan, Design Documents, etc.

## Project

**Restaurant Management System** — a web-based application for managing table bookings, food ordering, and menu management for a single restaurant outlet.

- **Backend:** Python (Django REST Framework)
- **Real-time layer:** Node.js (WebSocket / Socket.io) for live order-status updates
- **Author:** Abhay Dubey H (PES1UG24CS551), Dept. of Computer Science and Engineering, PES University

## Repository Structure

```
project-documentation/
├── .github/
│   └── workflows/
│       └── readme-reminder.yml
├── SRS and Test Plan Details/
│   ├── SRS/
│   │   ├── SRS - Restaurant Management System.docx
│   │   └── SRS - Restaurant Management System.pdf
│   └── Test-Plan/
│       ├── Test-Plan - Restaurant Management System.docx
│       └── Test-Plan - Restaurant Management System.pdf
├── Software Design And Architecture Specification/
│   ├── SAD- Restaurant Management System.docx
│   └── SAD- Restaurant Management System.pdf
├── Test cases related update for Test plan/
│   └── UpdateThemHere
└── README.md
```

## Documents

| Document | Status | Description |
|---|---|---|
| Software Requirements Specification (SRS) | ✅ Added | Functional & non-functional requirements, system features (Table Booking, Menu Management, Ordering & Tracking, Auth), and requirement traceability matrix. |
| Test Plan | ✅ Complete | Test strategy and functional test cases mapped to SRS requirements (REQ-1 → REQ-14). |
| Software Architecture and Design Specification (SAD) | ✅ Complete | Architecture, data design, security design, APIs, sequence diagrams, error handling, deployment view, and requirements traceability. |

## SAD Summary

The SAD defines an implementable, real-world design for the Restaurant Management System. It uses Django REST Framework for business logic and database transactions, Node.js and Socket.io for live order-status updates, and a relational database for durable booking and order data.

The design includes safeguards against double booking, unavailable menu items at checkout, unauthorized actions, session expiry, and missed WebSocket updates. The UML component diagram uses proper component notation with provided lollipop interfaces and required socket interfaces for REST API, real-time updates, event publishing, and database access.

## Conventions

- **File naming:** `<Document Type> - <Project Name>.<ext>` (e.g. `SRS - Restaurant Management System.docx`).
- **Revision history:** every document should carry its own Revision History table for tracked changes.
- **Traceability:** requirement IDs introduced in the SRS (`REQ-1` … `REQ-14`) should be reused as-is in the Test Plan and Design Documents so items stay traceable across all three.
- **Format:** `.docx` for formal deliverables; `.md` acceptable for lighter-weight or working documents.

## Status

| Milestone | Status |
|---|---|
| SRS drafted and reviewed | ✅ Complete |
| Test Plan | ✅ Complete |
| SAD prepared and reviewed | ✅ Complete |
