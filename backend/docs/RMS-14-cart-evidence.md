# RMS-14 / issue #20

Session-backed customer-only /api/cart (GET/POST replace/DELETE clear), protected by existing CSRF/session. Stores item IDs and positive whole quantities (1–99, at most 100 distinct lines); never trusts client prices. /cart/ shows current provisional totals, editing/removal, takeaway or booking context, preserved valid contents on errors. /menu/ adds only available items. Server checkout/confirmation belongs to RMS15; this isolated PR intentionally cannot place an order yet. Real currency is not prescribed by baseline; prices display as amounts without inventing currency.

Tests cover add/edit/remove/totals, empty and invalid quantities, unavailable items, role/identity. SQLite local checks and JavaScript syntax recorded in PR. Full browser/device and release acceptance pending.
