# Testing Checklist (UAT)

### Pairing
- Generate pair token → Agent pairs → agent_id + agent_token stored.

### Registration
- Agent starts Appium for each configured device (unique ports).
- Each device gets distinct `public_url` via tunnel.
- Devices table updated with `public_url`, `online=true`.

### Running
- Start Posting with template → IG/Threads opens, actions execute, progress updates.
- Warmup plan day 1 executes; day pointer persists.

### Negatives
- Kill Agent → device goes Offline within 90 s; Start returns 503.
- Wrong UDID → Start returns 400 with helpful message.
- Tunnel down → Start returns 503 "Tunnel unreachable".

### No localhost
- Confirm logs show `Creating session via: https://…` (not http://localhost).
