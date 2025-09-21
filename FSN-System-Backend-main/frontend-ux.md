# Frontend UX (Next.js)

## Pages / Components
1. **Templates / Create Template**
   - Form fields = columns in `templates_posting`.
   - Upload buttons store files to object storage; save URLs in DB.

2. **Warmup / Create Warmup**
   - Dynamic list of days; each day has actions (scroll, likes, follows, comments, stories, posts).
   - Save compact JSON to `templates_warmup.days_json`.

3. **Devices / Add Device**
   - Fields: name, UDID, appium_port, wda_port, mjpeg_port, wda_bundle_id, device_type, assigned_model.
   - Validation: all three ports must be unique across devices of the license.

4. **Accounts / Add Account**
   - Fields: platform, username, auth method, password, model, device assignment, notes.

5. **Running**
   - Cards per device: show status (Running/Paused/Stopped/Error), progress bar, last action, current step, attached account count.
   - Buttons: Start, Stop, Retry, View Logs.
   - Implement polling (e.g., 2–5 s) or WS to `/runs/{run_id}` for progress.

## API Wiring
- All forms call backend REST endpoints from `backend-api.md`.
- Running:  
  - **Start** → POST `/run/posting` or `/run/warmup` with selected template/account.  
  - Keep `run_id` in state and subscribe to progress.  
  - **Retry** just calls Start again when status = error/stopped.

## UX States
- Device **Offline**: disable Start, show reason ("Agent offline / no tunnel").
- Showing Endpoint: render short form of `public_url` on device card (for debug).
- File uploads: show "synced" state once URL saved.
