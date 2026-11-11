# RMS-19 / issue #26 — reconnect recovery

| Source | Executable | Result |
|---|---|---|
| REQ-10, SAD 5.5; added reconnect/stale/expiry cases | `realtime/test/tracking.test.js` | Four targeted tests passed; full Node suite 6/6 passed |
| Actual browser recovery with PostgreSQL/Django/Node | `orders.test_render_latency.RenderLatencyTests` in dependent PR #62 | Run 41188297526 passed |

Tracking retries transport failures with bounded exponential backoff. Every reconnect uses the existing authorized server handshake/owned room subscription, then reads owned REST state. Strict version advancement rejects late REST, duplicate and stale events. REST polling remains active during Node/client outages. Explicit server authorization revocation and REST 401/403/404 stop live resubscription and require fresh login/access. Page teardown clears timers.

Run `cd realtime && npm ci && npm test` for deterministic cases covering delayed REST races, stale/duplicate/wrong-order events, expiry, server revocation and absent Node client. Cumulative PostgreSQL foundation run 41187564465 also passed.

The adjacent RMS-19-browser-reconnect.json comes from the actual Chromium run in PR #62: Node was terminated, a committed Preparing update was recovered through REST, Node restarted on the same endpoint, the client reconnected, Served arrived live, and an expired session required login. Source and timings are retained in PR #62, including its common-clock timing method.

Browser run: https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/41188297526

PR #59 is stacked on #53; PR #62 adds browser acceptance on top of #59. Independent teammate review, dependency merges and retargeting to main remain required. The service remains same-origin and uses existing authorization; no public deployment is included.
