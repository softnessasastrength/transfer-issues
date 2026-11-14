# Privacy-first journey verification

**Status:** user-approved product requirement, implementation pending. Captured 2026-11-12.

## Governing principle

**Use the minimum data necessary to verify a journey; keep the minimum data necessary to display its history; put retention, collection, export and deletion under the user's control.** No server account, cloud sync, advertising identifier, or third-party analytics is required for core functionality. Offline verification is the default architecture target.

## User-selectable modes

1. **Manual only (privacy-preserving default on first install):** no passive GPS recording. User can add or confirm completed journeys manually.
2. **Verify journeys (explicit opt-in):** with a clear in-app start/stop control, process temporary location and optionally motion/activity observations locally to match plausible transit legs. Retain a compact journey record and evidence category/confidence; discard raw location observations promptly after classification and user review. Do not start collection simply because the user enabled pace learning.
3. **Detailed route recording (separate explicit opt-in):** store a user's actual GPS trace locally for chosen journeys. Show storage/retention implications, per-trip deletion, bulk deletion and export. This must never be required for basic journey verification.

Permissions are necessary but not sufficient consent. Runtime Android/iOS permission prompts must follow a clear in-app explanation; changing app mode or withdrawing consent stops future collection. Avoid background location for MVP; if later needed, separately justify and request it with platform-compliant disclosures and visible recording indicators.

## Verification model

- Correlate timestamped, accuracy-filtered observations with locally available route geometry, stop sequence, scheduled service windows and movement/activity context.
- Classify evidence as **user confirmed**, **probable sensor match**, **uncertain**, or **manual recollection**. GPS proximity alone does not prove vehicle boarding or a specific trip.
- Ambiguous overlapping bus routes, parallel streets, service disruptions, GPS drift, vehicle rides, and missing/expired feeds should prompt review or leave the journey unverified.
- A planned itinerary is never automatically a completed journey.
- Record only minimally necessary metadata: local journey ID, date/time precision, leg route/mode/stop references where credible, verification category, optional confidence/quality indicator, and user notes. Avoid retaining raw location coordinates unless detailed recording was specifically enabled.
- Preserve historical source/version provenance; do not reconstruct a supposed exact GPS trace from published GTFS shapes.
- Permit correction or rejection of any inferred journey without punitive UI or hidden retained copy.

## Data lifecycle and controls

- In-memory short-lived observation buffer while actively verifying; discard on session end, timeout, rejection or permission withdrawal. If crash recovery requires persistence, design a separately documented encrypted, bounded-TTL buffer with explicit opt-in. Never silently persist raw traces.
- App-private storage for retained records, and OS-backed encryption where appropriate; minimize backups that could unintentionally sync location history. User must know if device backup or export contains journey records.
- No logging of precise location, raw sensor samples, identifiers or personal journey records in production diagnostics, crash reports or analytics. Development verbosity may include synthetic test data and non-sensitive event counts; never ship debug location logs by accident.
- User controls: view collected data, pause recording, change mode, delete single trip, clear history, delete any detailed traces, export/import local records, and reset all personalization.
- No third-party telemetry, marketing SDKs, advertising SDKs, remote profiling, or silent cloud uploads without separately documented informed consent and product authorization.
- Avoid location permission when manual entry suffices; request foreground location only when an actual feature needs it.
- Public release must have a plain-language privacy policy, accurate Google Play Data safety disclosures, permission review, backup/export review and independent test of deletion/retention behavior. Never promise 'zero data collection' if permissions or optional telemetry contradict it.

## Privacy-preserving acceptance tests

1. Fresh install defaults to Manual only; no sensor/location collection occurs until an explicit mode selection and session start.
2. Location permission denied/revoked: manual journey history and browsing still work.
3. Verify mode with synthetic GPS observations yields a probable journey without retaining raw points after finalization.
4. GPS near two overlapping routes yields an uncertain result rather than false proof of boarding.
5. App backgrounded or verification stopped: collection ceases according to documented foreground policy.
6. Consent withdrawal discards transient observations and prevents new ones.
7. Detailed trace is absent unless separate opt-in; deleting a trace removes stored coordinates without deleting the summary unless requested.
8. Production logging/crash instrumentation never emits GPS coordinates or personal journey records.
9. Export/import and device backup behavior are transparent, controllable, and tested.
10. Full-history deletion and per-journey deletion persist after restart; no silent copies remain in app-controlled stores.
11. All verification, storage and deletion paths work without network connectivity.
12. UI shows evidence categories and lets the user reject or correct sensor matches.
13. Test permission differences and foreground lifecycle on actual Android and iOS devices before claiming verified behavior.

## Interaction with other specifications

- `docs/features/journey-history.md`: confirmed history map and route coverage; never conflate probable sensor match with user confirmation.
- `docs/features/adaptive-transfer-timing.md`: speed calibration consent is separate from trip recording consent; pace profiles contain aggregates only.
- `docs/launch/release-checklist.md`: publication requires privacy review, accurate disclosures and removal of debug logging.

**No implementation or real sensor validation occurs in this documentation change.**
