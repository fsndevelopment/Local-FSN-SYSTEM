# Selectors & UI Actions (Skeleton)

## Instagram (iOS)
- App ID: `com.instagram.iphone`
- Common actions:
  - Activate app
  - Open composer
  - Attach photo from camera roll
  - Set caption (paste)
  - Publish
- Keep iOS accessibility identifiers & fallback XPath stored here.
- Provide a tiny wrapper: `ig.tap(selector)`, `ig.type(selector, text)`, `ig.wait(selector, timeout)`.

## Threads (iOS)
- App ID: `com.barp.Trident` (example; confirm actual bundle)
- Actions: new thread, paste text/media, post, like, follow.
