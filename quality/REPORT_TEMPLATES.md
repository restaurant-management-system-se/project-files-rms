# Execution and review records

Copy a template for an actual execution. Empty fields mean Pending, never Pass. Keep credentials/session cookies out of logs and screenshots. Link immutable source commits and workflow runs/artifacts.

## Manual execution record

- Canonical test ID and source variant(s):
- Requirement IDs:
- Build commit and dirty state:
- Environment, PostgreSQL version, browser/version, deployment URL:
- Tester and UTC start/end:
- Preconditions and data identifiers:
- Exact steps actually performed:
- Expected result:
- Actual observations:
- Result: Not Executed / Blocked / Failed / Passed
- Evidence path or workflow artifact:
- Defect links and remaining scope:

## Defect report

- Defect ID / GitHub issue:
- Requirement and test ID:
- Feature owner:
- Severity and priority:
- Build/environment:
- Reproduction steps:
- Expected versus observed behavior:
- Logs/screenshots (redacted):
- Status, fix PR and retest evidence:

## Security validation report

- Build, deployment and tester:
- SV_01 through SV_10: list each separately with actual scope, result and evidence:
- TLS/browser/proxy/Socket.io coverage:
- Known untested endpoints, actors and payloads:
- Open defects, severity and owners:
- Release decision: Pending until all security procedures pass:

## Test summary report

- Build, environment, exact commands and UTC window:
- Automated executables: passed / failed / error / skipped:
- Canonical planned procedures: 58 total; passed / failed / blocked / Not Executed:
- Requirements: 29 mapped; complete executed coverage versus partial subcases:
- Security, PERF-1/2/3, usability, browser and restart evidence:
- Open critical/high defects and untriaged limitations:
- Exit criteria assessment and explicit unmet conditions:
- Independent reviewer and owner sign-off (Pending until supplied):

Test Plan exit gate: 100% planned cases executed, zero critical/high open defects, all SV pass, all PERF thresholds met, 100% requirement coverage and every acceptance criterion satisfied. A green CI run is regression evidence only; it is not release acceptance.
