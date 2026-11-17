# RMS-12 / issue #18

Sprint 2: 26–31 October 2026. Prasanna owns this implementation. Reuses main 9b4f49f database/auth. Adds MenuItem.description (blank default, 2000-character limit) in migration 0002 without changing User/Booking.

Admin UI: /manage/menu/. API: GET/POST /api/admin/menu; GET/PATCH/DELETE /api/admin/menu/<id>. Uses existing session/CSRF and Admin role. Exact categories, trimmed nonempty name, two-decimal nonnegative price, bounded description. Read-only/unknown fields rejected. Referenced deletes set available=false; PROTECT history remains. Unreferenced deletes remove the item.

Audit integration: when auditlog from PR46 is installed, mutations use audited_change in the same transaction. Description-only changes explicitly record one MenuUpdate because the existing RMS23 signal watches legacy fields. Full audit-stack integration must be checked before accepting RMS23; no team agreement is invented.

Executed local menu tests: 4/4 passed (0.055s), SQLite; no PostgreSQL concurrency claim. Full PostgreSQL CI and independent review remain pending. Demo: Admin login, create/edit Soup, mark it unavailable, delete an unreferenced item; referenced item is retained. Staff/Customer/anonymous mutations are denied. Browser/device/release acceptance is separate.
