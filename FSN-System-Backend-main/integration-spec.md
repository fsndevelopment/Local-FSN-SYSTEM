# FSN Integration Spec (End-to-End)

## Goal
Clients log in at **fsndevelopment.com**, run a **Mac Device Agent**, and control their **real iPhone(s)** from the web:
- Frontend stores device config (UDID, ports) and posting/warmup templates.
- Backend runs jobs and talks to devices through the Agent's tunneled Appium endpoints.
- One click **Start** on the Running page = launch of posting/warmup tasks on a chosen device.

## High-Level Architecture
Frontend (Netlify) → Backend (Render, FastAPI) → Agent (macOS app on client) → Appium → iPhone (USB)

- Backend never uses `localhost`; it always uses the Agent's **public Appium URL** (via tunnel).
- One **Appium server per device** (unique ports & tunnel URL per device).

## Core Flows

### A) Pairing an Agent
1. Frontend: `POST /api/agents/pair-token { license_id }` → returns short-lived `pair_token` + QR string.
2. Agent asks user to paste/scan the token → `POST /api/agents/pair { pair_token, agent_name, platform, app_version }`.
3. Backend returns **agent_token (JWT)** + `agent_id` → Agent stores token securely.

### B) Agent Registers Devices
1. Agent fetches devices for the license (`GET /api/devices?license_id=...`).
2. For each device:
   - Start Appium on `device.appium_port` with base path `/wd/hub`.
   - Start tunnel for that port and obtain `public_url` (HTTPS).
   - `POST /api/agents/register` (Bearer agent_token) with:
     - `udid`, `local_appium_port`, `public_url`, `appium_base_path`, `wda_local_port`, `mjpeg_port`.
3. Agent sends `POST /api/agents/heartbeat` every ~10s (with UDID list).

### C) Start a Run (Posting or Warmup)
1. Frontend Running page → `POST /api/run/posting { license_id, udid, template_id }`
   or `POST /api/run/warmup { license_id, udid, warmup_id }`.
2. Backend loads the device row, ensures `public_url` + `online`, builds:
   - `remote = device.public_url + device.appium_base_path` (e.g., `https://…/wd/hub`)
   - iOS capabilities using UDID/WDA/MJPEG ports from DB.
3. Backend instantiates WebDriver and executes the **job plan** defined by the template(s).
4. Progress, logs, and errors stream back to the frontend (SSE/WebSocket or polling).

## Required Guarantees
- **No localhost in production** for device control.
- **Per-device isolation**: unique Appium/WDA/MJPEG ports & tunnel URL per UDID.
- **Heartbeat semantics**: Agent becomes Offline if no heartbeat within 60–90 s.
- **Idempotent Start**: backend prevents double-starts for the same device run_id.

## Definition of Done
- Pairing, Register, Heartbeat implemented with JWT auth.
- Devices updated with `public_url`, `agent_id`, `online`, `last_seen`.
- Running page Start launches a real Appium session via `public_url`, uses FE ports & UDID.
- Posting/Warmup execution reads template configs and updates progress.
- Clear errors & Retry path.
