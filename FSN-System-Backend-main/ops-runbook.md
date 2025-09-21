# Ops Runbook

## Common Checks
- Agent online? → `/agents/active/{license}` shows `online=true`.
- Tunnel alive? → `curl https://public_url/status` from server (should return Appium JSON).
- WDA built? → first-time Xcode run per iPhone.

## Port Conflicts
- Symptom: Appium fails to bind port.
- Fix: Change `appium_port` in Devices or let agent auto-assign (if feature enabled).

## Device Offline
- Agent not heartbeating → restart Agent; check USB cable; trust prompt.
- Backend will flip to Offline after `HEARTBEAT_TIMEOUT_SECONDS`.

## Reset Stuck Runs
- Use `POST /runs/{run_id}/stop`, then Retry.
