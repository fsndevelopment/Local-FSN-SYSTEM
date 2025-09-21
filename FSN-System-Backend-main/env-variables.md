# Environment Variables

## Backend (Render)
- `DATABASE_URL`
- `JWT_SECRET`
- `APP_BASE_URL` (e.g., https://fsndevelopment.com)
- `DEFAULT_APPIUM_BASE_PATH` (/wd/hub)
- `HEARTBEAT_TIMEOUT_SECONDS` (e.g., 90)
- `LOG_LEVEL` (info|debug)

## Frontend (Netlify)
- `NEXT_PUBLIC_API_URL` (backend base URL)

## Agent (macOS)
- `FSN_BACKEND_BASE` (backend base URL)
- `NGROK_AUTHTOKEN` (optional; if present, use ngrok; else cloudflared)
