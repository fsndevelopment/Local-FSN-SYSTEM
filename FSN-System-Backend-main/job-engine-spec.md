# Job Engine Spec (Posting & Warmup)

## Executor
- One executor per run (`run_id`), single device at a time.
- Steps are generated from templates (deterministic plan).
- Emits progress events and structured logs → `run_logs`.

## Posting Plan (example)
1. Activate app (Threads/Instagram).
2. If `photos_per_day > 0`: open composer → attach photo from storage → set caption from captions file → publish.
3. If `text_posts_per_day > 0`: create text post(s).
4. Perform actions: likes/follows based on per-day limits.
5. Scrolling/safety sleeps based on `scrolling_minutes`.
6. Mark run success when all steps complete.

## Warmup Plan
- Iterate `days_json` (Day 1..N).
- For each day, execute: scroll x min, likes y, follows z, comments s, stories t, posts p (randomized within ±10% unless disabled).
- Persist "current day index" per account+device to continue next run.

## Safety & Delays
- Backoff on app errors, CAPTCHA, rate limits.
- Randomized small delays between actions (100–800 ms); larger sleeps where configured.
- Hard timeout per run (e.g., 45 min) → mark error.

## Error Classes
- DeviceOffline, TunnelUnreachable, AppiumSessionError, ElementNotFound, AuthFailed, MediaMissing.
- Retry policy: automatic retry for transient network errors (up to 3); otherwise surface error with `Retry` button.

## Outputs
- `runs.status`, `progress_pct`, `current_step`, `last_action`, `error_text`.
- `run_logs` rows with payloads (selectors, timing, media path used).

## Selectors
- Keep selectors in a central module per platform & app version.
- Provide feature flags to switch fallback selectors if UI changes.
