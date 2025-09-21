# Security & Auth

## Tokens
- **User JWT**: normal web calls (scoped to user & license_id).
- **Agent JWT**: returned by `/agents/pair`, scoped to `license_id` & `agent_id`.
  - Used only on `/agents/register` and `/agents/heartbeat`.

## Validation
- Agent requests must include Bearer agent JWT.
- `/run/*` verifies the requested `license_id` belongs to caller and device belongs to license.

## Transport
- All web/API over HTTPS.
- Tunnel endpoints are HTTPS (cloudflared/ngrok).

## Hardening
- No `localhost` usage in production for device control.
- Validate `public_url` host against allowed patterns.
- Heartbeat timeout marks agents/devices offline.
- Store passwords encrypted at rest; never log secrets.
