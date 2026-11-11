# RMS-18 / issue #24

Django remains the only database/business owner. Status changes create a unique OrderEvent(order,version) in the same transaction and register an on_commit publisher. Failed transactions publish nothing; Node downtime leaves a committed outbox row. Trusted operator retries with `python manage.py publish_order_events` (100 per invocation); deployment scheduling remains an operator task. At-least-once delivery uses event ID/version; Node suppresses duplicate/older versions per connection. No reconnect/resync feature is claimed (Akul RMS19).

Run `npm ci && npm start` in realtime with RMS_REALTIME_KEY (>=32 random characters), RMS_DJANGO_URL (loopback HTTP or HTTPS), RMS_PUBLIC_ORIGIN (exact browser origin), PORT (default3000). Set Django RMS_REALTIME_KEY to same secret and RMS_REALTIME_INTERNAL_URL to private Node URL. No secrets in client or git. Same-origin reverse proxy must route /socket.io to Node and normal paths to Django; production HTTPS/WSS termination belongs to deployment issue #6. Do not expose /api/internal or Node /internal paths at the public edge. Default empty key fails closed and leaves events pending.

Node checks browser Origin and current Django /api/auth/session before handshake, periodically and before each delivery, then verifies active actor/order ownership/Staff/Admin role through a key-protected cookie-free Django endpoint. Background session check uses Noctowl's existing non-activity endpoint; it never extends idle time. Node has no DB credentials. Internal publishing uses constant-time shared-key comparison and resolves event UUID against committed Django data. Request/response/error logs never include session values. Disconnect after logout/expiry is bounded by the 1-second check; every delivery rechecks authorization.

Customer /orders/<id>/ fetches owned REST status then applies versioned events with textContent. Missing Node leaves saved REST status readable. Live connection errors instruct refresh; automated reconnect is RMS19. Checkout links to tracking; staff queue changes status. Tests include outbox rollback/retry, secrets/ownership and a real Django+Node PostgreSQL owned-room/cross-customer flow. Node unit tests use a synthetic negative fixture only; no fixture latency substitutes for browser render timing. Actual execution counts are recorded in PR.

Remaining acceptance: real deployed HTTPS/WSS, browser/device tests and commit-to-render timing under the stronger REQ10 and PERF2 wording require the agreed environment. No one-second universal/95th-percentile pass is claimed by implementing delivery; Akul RMS25 owns measured percentile evidence. See existing PENDING03/04/06; no source requirement or teammate approval is fabricated.

## Executed integration before publishing

Local full feature stack: 81 discovered, 60 passed, 21 skipped (PostgreSQL and optional audit-only), 1.218 seconds. Node service tests: 2/2 passed. Disposable merge with Noctowl audit head c14d446: 119 discovered, 78 passed, 41 PostgreSQL-only skipped, 1.692 seconds. Menu API audit capture including description-only edit passed. This does not prove PostgreSQL audit rollback/live delivery yet. CI reuses the existing single PostgreSQL service and runs the feature stack, then a disposable pinned RMS23 merge without committing/pushing any owner branch. It preserves logs; exact outcomes must be recorded from the run.

The workflow test prerequisites overlap Akul PR42's unmerged extension. Akul must review/resolve that shared workflow diff when retargeting; this does not claim an agreed pipeline change or implement a second pipeline.

## PostgreSQL execution completed — 28 October 2026

Published/tested live head: `bd1e3e58d3934e0f433f249912a3e41aa6eccf81`. All seven feature branches byte-matched their tested local source trees before the documentation-only update. [Run 40642103210](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/40642103210), job 122662354063, passed:

- Feature stack: **79 passed, 2 optional audit-stack tests skipped**; 81 discovered, 35.084 seconds.
- Disposable merge with pinned audit head `c14d4469a409003db99af322471ab2fb5f4f7751`: **118 passed, 1 SQLite-only test skipped**; 119 discovered, 39.937 seconds.
- Node service unit tests: **2 passed**, no failures/skips.

Real PostgreSQL + Django LiveServer + the actual Node server delivered committed Preparing version 2 to the owning customer and rejected another customer and an expired session. The session last_activity value was unchanged by socket authorization. Audit-stack endpoint tests passed menu create/description-only update/delete attribution, one status event on safe retry, and rollback of status/version/outbox on audit failure. Original booking/cancellation/staff races were included in the combined run. Fresh migrations, two demo seeds and migration consistency passed. Raw feature/audit logs are retained in the run artifact. Expected negative constraint tests produce database ERROR log entries; their assertions passed and they are not unhandled suite failures.

| Owned issue | PR | PostgreSQL run | Actual cumulative result |
|---|---|---|---|
| RMS12 / #18 | #47 | 40639798301 | 63/63 passed, 26.624s |
| RMS13 / #19 | #48 | 40640308326 | 65/65 passed, 16.624s |
| RMS14 / #20 | #49 | 40640583588 | 68/68 passed, 28.751s |
| RMS15 / #21 | #50 | 40640765198 | 72/72 passed, 18.165s |
| RMS16 / #22 | #51 | 40641063250 | 73/73 passed, 30.619s |
| RMS17 / #23 | #52 | 40641685307 | 76/76 passed, 32.326s; distinct Staff actors |
| RMS18 / #24 | #53 | 40642103210 | 79 passed/2 optional skips, then 118 passed/1 SQLite-only skip with audit |

These are cumulative regression executables, not a sum of independent canonical Test Plan procedures. All six earlier suites had no skips. Local smoke uses SQLite; concurrency evidence above uses PostgreSQL. Full planned-case execution, deployed security/browser acceptance and universal one-second/95th-percentile render timing remain unexecuted. PR53 stays draft; issues stay open/In Review until independent review and owner merge.

### Demonstration after reviewed dependency merges

1. Admin logs in at /login/ and opens /manage/menu/. Create Soup under Starters with description and price, edit it, and toggle availability.
2. Customer opens /menu/, adds available dishes, edits positive whole quantities at /cart/, and selects takeaway or their own confirmed booking.
3. Place the order; the server confirms a Received order with saved total and a tracking link. Repeating a network request with its UUID returns the same order.
4. Staff opens /staff/orders/, moves Received to Preparing then Served. With the documented Node service and same-origin proxy, the customer's /orders/<id>/ page receives committed versioned changes.
5. To demonstrate stale cart, add two dishes, have Admin disable one, then submit: no partial order is created. Remove the flagged dish and confirm the remaining contents.
6. With Noctowl's reviewed RMS23 installed, Admin views /admin/auditlog/auditevent/ for menu, booking and status actions. Referenced menu deletion preserves history by disabling the item.

Deployment blockers: configure private service URLs, a strong shared secret, same-origin HTTPS/WSS proxy and trusted retry scheduling; verify browser rendering/timing in that environment. Akul owns reconnect/resynchronization and percentile/load/restart evidence. No teammate issue is closed or merged by this work.
