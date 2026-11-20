# RMS-25 / issue #28 — committed status to rendered customer state

| Source | Executable | Result |
|---|---|---|
| PERF-2, IT_07 / ST_05 latency/lifecycle aspects | `orders.test_render_latency.RenderLatencyTests` | 20/20 observed updates within 1 second; nearest-rank p95 upper bound 112.075977 ms |
| Stronger REQ-10 each-update wording | Same raw observations | All 20 pass in this sample; not a universal guarantee |

Executed on PostgreSQL with the actual Django outbox, Node service, ephemeral same-origin HTTP/WebSocket test proxy and headless Chromium. Run 41188297526 passed after keeping synchronous Django ORM work on its own thread; no Django async safety guard was disabled.

Run: https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/41188297526

RMS-25-render-latency.json contains every synthetic order/version/status observation and the summary. A single Python perf_counter_ns clock starts inside transaction.on_commit immediately before dispatch, after the database transaction has committed. It ends after Chromium acknowledges a DOM mutation and two animation frames. Acknowledgement overhead is included, so measurements are conservative upper bounds and do not merely time emission. There is no cross-machine wall-clock subtraction.

The test makes two real transitions (Received -> Preparing -> Served) for each of ten orders. It also validates #26 through Node downtime, REST recovery of a missed state, restart/resubscription, live delivery and expiry requiring login. Its raw result is RMS-19-browser-reconnect.json.

Reproduce: install backend requirements and Python playwright, run `playwright install chromium`, run `npm ci` in realtime, then from backend run `RMS_RUN_BROWSER=1 python manage.py test orders.test_render_latency --verbosity=2` using PostgreSQL DB_* settings. Django owns the isolated test database and child processes are cleaned up. The acceptance workflow installs Chromium dependencies and preserves JSON even on failure. The cumulative foundation workflow also passes separately.

This proves the measured CI sample only, not public HTTPS/WSS deployment, every browser/device or all future updates. PR #62 depends on #59 and #53. Independent review, dependency merges, retargeting and owner merge remain required. The broader planned test cases have additional aspects outside this executable.
