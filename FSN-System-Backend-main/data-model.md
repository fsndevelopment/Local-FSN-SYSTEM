# FSN Data Model

## Tables

### licenses
- id (pk), owner_user_id, status, plan, created_at

### agents
- id (pk), license_id (fk), agent_name, platform, app_version
- last_seen (ts), is_online (bool), appium_base_path (text, default `/wd/hub`)

### devices
- id (pk), license_id (fk), name, udid (unique per license)
- assigned_model_id (nullable fk)
- appium_port (int), wda_port (int), mjpeg_port (int)
- public_url (text), agent_id (fk)
- appium_base_path (text, default `/wd/hub`)
- is_online (bool), last_seen (ts)
- device_type (enum: non_jb, jb)
- wda_bundle_id (text)
- notes (text), created_at

### models
- id, license_id, name, demographics/json (optional), created_at

### accounts
- id, license_id, platform (enum: threads, instagram)
- username, auth_method (enum: non_2fa, totp, sms), password_encrypted
- model_id (fk), device_id (fk), notes
- created_at

### templates_posting
- id, license_id, platform
- name, photos_per_day (int), text_posts_per_day (int)
- follows_per_day (int), likes_per_day (int)
- captions_file_url (nullable), photos_folder_url (nullable)
- scrolling_minutes (int), created_at

### templates_warmup
- id, license_id, platform, name, description
- days_json (array of day objects: {scroll, likes, follows, comments, stories, posts})

### runs
- run_id (uuid), license_id, device_id, account_id (nullable), type (posting|warmup)
- template_id (fk), warmup_id (fk), started_at, finished_at (nullable)
- status (queued|running|paused|stopped|success|error)
- progress_pct (float), current_step (text), last_action (text), error_text (text)

### run_logs
- id, run_id (fk), ts, level (info|warn|error), message (text), payload_json

## Indices
- devices(license_id, udid), agents(license_id, is_online), runs(license_id, device_id, status)
