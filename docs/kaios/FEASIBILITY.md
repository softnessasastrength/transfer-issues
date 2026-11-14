# KaiOS 3.1 feasibility and qualification (draft)

Target: BLU FLEX B300V, 240×320 keypad display. **Hardware support unverified.**

## Evidence
- KaiOS 3.x uses Gecko 84, modern web manifest (`manifest.webmanifest`), and supports PWAs according to KaiOS.dev's version comparison: https://kaios.dev/faq/
- KaiOS 3.0 architecture documents a changed app manager and HTTP-based app origins: https://developer.kaiostech.com/docs/sfp-3.0/introduction/overview/
- KaiOS 3.x normally disables end-user debugging and straightforward sideloading. Community JScalated research (June 2026, updated October) describes device/firmware-dependent privileged JavaScript/ADB techniques, **not** a verified B300V installation route: https://kaios.dev/2026/06/jscalated-from-the-browser-to-adb-on-kaios-3.1/
- No firmware modification, protection bypass, ADB assumption or app-store submission is authorized.

## Proposed architecture
```
KaiOS HTML/CSS/JS shell
  | localStorage: user-approved saved itineraries + bounded validated snapshots
  | fetch: HTTPS, same-origin proxy when needed
Transit Atlas /api/v1/ meta, coverage, departures, plan
  | existing Python/SQLite engine
```
Never expose the existing loopback-only unauthenticated development server to the internet. Production connectivity requires a separate authenticated HTTPS proxy and reviewed CORS policy. The device's own localhost is **not** the Mac/Termux server. Version compatibility endpoints only after contract tests prove a need.

## First software milestones
1. Browser-only static 240×320 keypad shell with ArrowUp/Down, Enter, Escape/Backspace, softkey mappings; no framework.
2. Read-only API adapter and fixture-driven departures/planner with source/expiry/error banners; never represent scheduled results as live.
3. Saved journeys, explicit consent to cache data, export/clear controls; no silent network downloads or eviction of user-selected packs.
4. Browser automated tests (keypad, XSS-safe text rendering, offline startup, timeout/HTTP error, stale cache) and Crostini/desktop Linux reproducibility.
5. Separate hardware qualification. Store packaging, debugging and installation remain **blocked pending device/firmware verification**.

## Device performance budgets (targets, not measurements)
- Initial HTML/CSS/JS shell <= 100 KiB uncompressed; zero external JS frameworks.
- At most one API request per explicit user action, except explicit multi-step sync.
- Initial list <= 30 visible rows, paginated; no remote map tiles in core flows.
- Keep cached response snapshots bounded by validated storage availability; never silently delete user-created journeys. Warn if quota exhausted.
- Avoid background polling, backend inference on device, unnecessary geolocation permissions.

## Qualification checklist
- [ ] Record B300V hardware revision, KaiOS build, carrier, browser UA, free storage and actual display geometry (no secrets).
- [ ] Confirm URL entry and ordinary hosted-page rendering without installing an app.
- [ ] Test directional/Enter/Back/left-right softkeys; record key values and focus behavior.
- [ ] Test network, HTTPS certificate chain, fetch/CORS, offline restart and storage persistence.
- [ ] Measure launch time, heap/GC symptoms, battery drain, page transitions and 30-row scroll.
- [ ] Confirm developer-access method from vendor-supported documentation, or record unavailable.
- [ ] Independently confirm install/upgrade/removal path before declaring installable.
- [ ] Validate real timetable/coverage freshness and no-result messages against backend.
- [ ] No firmware edits, no exploit-based steps, no store publication.

## Acceptance boundary
Desktop browser simulation is not Gecko 84 or physical B300V acceptance. Offline cached departures are informational snapshots; a truly offline route-planning engine is not available in this thin client. The project-wide offline-first policy still applies: never claim full offline routing, silently shrink user-selected network packs, or trade away Android offline behavior. Investigate a validated portable route pack later if the B300V can support it.
