# FSN Backend API (FastAPI)

> All endpoints are under `/api`. Use JWTs:
> - User JWT for web (normal auth).
> - **Agent JWT** for `/agents/*` (scoped to `license_id`).

## Agents

### POST `/agents/pair-token`
Body: `{ "license_id": "LIC-..." }`  
Return: `{ "pair_token": "...", "qr_payload": "fsn://pair?token=..." , "expires_at": ISO8601 }`

### POST `/agents/pair`
Body: `{ "pair_token": "...", "agent_name": "Mac", "platform": "macOS", "app_version": "1.0.0" }`  
Return: `{ "agent_id": 123, "agent_token": "JWT", "appium_base_path": "/wd/hub" }`

### POST `/agents/register` (Bearer **agent_token**)
Body:
```json
{ 
  "agent_name": "Mac", 
  "license_id": "LIC-...", 
  "endpoints": [ 
    { 
      "udid": "...", 
      "local_appium_port": 4735, 
      "public_url": "https://...", 
      "appium_base_path": "/wd/hub", 
      "wda_local_port": 8100, 
      "mjpeg_port": 9100 
    } 
  ] 
}
```
Return: { "agent_id": 123 }

### POST `/agents/heartbeat` (Bearer agent_token)
Body: { "agent_id": 123, "udids": ["..."], "uptime": 1234, "version": "1.0.0" }  
Return: { "ok": true }

### GET `/agents/active/{license_id}`
Return: the active agent object plus its device endpoints (online).

## Devices
### GET `/devices`
Query: license_id=... → returns devices rows (see schema in data-model.md).

### PATCH `/devices/{device_id}`
Allow updating appium_port, wda_port, mjpeg_port, assigned_model_id, etc.

## Run
### POST `/run/posting`
Body: { "license_id": "LIC-...", "udid": "0000...", "template_id": 42, "account_id": 99 }  
Behavior:
- Validate device online; get public_url, ports, UDID.
- Build WebDriver → execute Posting Plan resolved from template & account.
- Stream logs and progress. Return { "run_id": "uuid" }.

### POST `/run/warmup`
Body: { "license_id": "LIC-...", "udid": "0000...", "warmup_id": 5 }  
Same semantics with the Warmup Plan.

### GET `/runs/{run_id}`
Return progress, current step, last action, error (if any).

### POST `/runs/{run_id}/stop`
Gracefully terminate execution and quit session.

## Errors
- 400 invalid input (UDID missing, config mismatch)
- 401/403 auth issues
- 404 not found
- 409 run already in progress for device
- 503 no active agent / device offline / tunnel unreachable
