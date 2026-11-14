# Browser UI agent instructions

Read root `AGENTS.md`, `ROADMAP.md`, `docs/agents/README.md`, and `docs/launch/product-vision.md`.

Scope: `web/` and necessary documented API interfaces. Preserve existing desktop and Termux behavior, theme/units, location opt-in, route overlay, journal and backup workflows.

Map-first exploration and practical trip planning are equally important. Display all available routes with safe CSS colors and text labels; avoid inserting untrusted GTFS fields as HTML. Use DOM textContent or equivalent escaping for route labels/tooltips. Keep large-network overlays responsive and bounded; prefer efficient bulk geometry endpoints after validating contracts.

Do not imply the raster OpenStreetMap tile URL works offline. Offline map packaging must use properly licensed data. Preserve source/expiry warnings. Test responsive layout and keyboard/touch interaction when tools permit; document when browser/device tests are unavailable.
