# RMS-23 / issue #9 — privileged audit service

Owner and publishing account: Noctowl-Abhay. Sprint 2: 26–31 October 2026, work performed from 28 October. Separate PR stacked on Captain's RMS-11 PR #44; retarget after its reviewed owner merge. Do not self-review, merge or close this issue while dependencies remain.

## Implemented scope

- New auditlog app/migration stores actor ID, allowlisted action, model label, record ID, timestamp and optional unique booking-override source. No password/token, customer name/email, arbitrary JSON payload or free-text reason is copied. Original booking reason remains in BookingOverride and can be traced through the protected source link.
- Staff booking Create/Cancel override post-save capture automatically writes one central event in the same PostgreSQL transaction, including retries and rollback on central audit failure. Source identity and original actor/time are derived from persisted override evidence. Backfill is idempotent and handles historical actors without inventing current authorization.
- `with auditlog.services.audited_change(actor): ...` is the explicit menu/order integration adapter. It locks/revalidates a Staff/Admin actor and encloses business state and event writes in one atomic transaction. Menu create/update/delete require Admin. Persisted order-status changes allow Staff/Admin. No-op saves or unsaved status fields do not create success events. Nested/error contexts reset correctly. ORM bulk update/delete bypasses instance hooks: feature owners must not use uninstrumented bulk writes for privileged changes.
- Admin-only Django Admin viewing is readonly. Model/QuerySet save/update/delete paths deny edits/removal; actor and booking source references use PROTECT. No public audit mutation API exists. These are application-layer protections, not a claim that a database superuser cannot tamper with data.
- Trusted-operator `python manage.py audit_maintenance` defaults to dry run. `--execute --backfill` fills missing booking events and deletes only events strictly older than 90 days, preserving the exact boundary instant and all younger events. No public endpoint exposes retention. Deploy operators must schedule the command in their existing environment; no server/cron configuration is invented.

## Remaining integration blocker

RMS-12 menu management (#18) and RMS-17 order-status services (#23) do not exist on the inspected main/feature branches. This PR provides and tests their adapter using the actual MenuItem/Order models, but does not implement or take over Prasanna's business endpoints. The feature owner must wrap each authorized instance mutation in audited_change and run complete end-to-end event-coverage tests, including checking no bulk bypass. Therefore **full #9 acceptance is blocked by #18/#23**, even when this PR's service tests pass. A proposal and runnable adapter are not teammate agreement or full event completeness.

## Verification and demo

Local combined suite: 97 discovered, 64 passed, 33 PostgreSQL-only skipped, 1.315s. Added accounts/test_audit.py so the existing CI test-discovery command includes audit checks without changing Akul's workflow. Tests cover menu action attribution, real order status changes, no-op/update_fields behavior, minimal fields, denied roles, immutable records/admin access, business/audit failure rollback, strict 90-day boundary and dry run. PostgreSQL integration tests exercise actual staff booking endpoints, no duplicate retry events, central audit failure rollback and idempotent backfill. Exact CI run/revision/counts will be recorded on the PR after execution.

Demo after migration: Admin provisions Staff, Staff creates/cancels through /staff/bookings/, Admin views /admin/auditlog/auditevent/. Each successful override appears once with actor/action/record/time. Customer and Staff cannot edit/delete/view central Admin audit screens. The command dry run reports expired/missing entries without mutation. Do not present synthetic adapter tests as deployed menu/order end-to-end acceptance.

No existing User/MenuItem/Order/Booking fields change. Settings only registers the new app; existing authentication and business APIs retain behavior. Existing booking audit records are reused, not recreated. CI/deployment and menu/order ownership remain unchanged.
