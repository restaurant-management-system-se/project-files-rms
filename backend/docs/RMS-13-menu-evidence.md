# RMS-13 / issue #19

Depends on RMS12. GET /api/menu is public per DEV04, read-only and no-store; categories always include Starters/Main Course/Desserts/Beverages with empty arrays as appropriate. Only available items appear, ordered by name/id; each fresh GET reads saved state. /menu/ renders responsive cards using textContent for names/descriptions/prices and clear empty/error states. Cart integration belongs to the next issue.

Tests verify grouping, empty menu, next-fetch changes, unavailable exclusion, public write denial and safe responsive template. Local SQLite execution recorded in PR; PostgreSQL CI and full human browser/device acceptance pending. Demo: edit availability as Admin then fetch/refresh /menu/.
