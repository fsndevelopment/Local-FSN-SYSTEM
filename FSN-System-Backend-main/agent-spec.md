# FSN Device Agent (macOS) Spec

## Purpose
A lightweight menubar (or console) app that:
- Pairs itself to a license (one-time).
- Starts Appium per configured device (using DB ports).
- Creates one tunnel per Appium port and registers public URLs.
- Sends periodic heartbeats and restarts components if they die.

## Dependencies (macOS)
- Xcode + CLT (for WebDriverAgent)
- `libimobiledevice`, `usbmuxd`, `ios-deploy`
- Node: `npm i -g appium @appium/doctor appium-xcuitest-driver`
- Tunnel: **cloudflared** (default) or **ngrok** (if `NGROK_AUTHTOKEN` is present)

## Persistent Storage
- `~/Library/Application Support/FSN/agent.json`  
  ```json
  { "agent_token": "...", "agent_id": 123, "license_id": "LIC-..." }
  ```

## State Machine
- **No Token** → show Pair UI → POST /api/agents/pair → store agent_token.
- **With Token**:
  - Query /api/devices?license_id=....
  - For each device with UDID present locally:
    - Start Appium: appium --port {appium_port} --base-path /wd/hub --allow-cors.
    - Start tunnel for that port → parse public_url.
    - POST /api/agents/register with endpoint list.
    - Start heartbeat loop (10 s).
    - Monitor child processes; restart on failure.

## Register Payload (per device)
```json
{
  "agent_name": "MacBook-Pro",
  "license_id": "LIC-123",
  "endpoints": [
    {
      "udid": "00008110-...",
      "local_appium_port": 4735,
      "public_url": "https://abc-4735.trycloudflare.com",
      "appium_base_path": "/wd/hub",
      "wda_local_port": 8100,
      "mjpeg_port": 9100
    }
  ]
}
```

## Heartbeat
- POST /api/agents/heartbeat (Bearer agent_token)
- Body: { "agent_id": 123, "udids": ["…","…"], "uptime": 1234, "version": "1.0.x" }

## UX (Menubar)
- Status: Online/Offline, device list, each with Appium port + public URL.
- Buttons: Pair / Unpair, Restart Appium, Restart Tunnel, Open Logs.
- WDA Setup helper: open WDA Xcode project instructions.

## Error Handling
- If tunnel not obtained in 30 s → retry with backoff.
- If Appium port in use → auto-pick next free port and PATCH device (optional flag).
- If UDID missing locally → mark device "disconnected" in Register.
