# Adaptive Transfer Timing — feature proposal

**Status:** proposed, not implemented. **Requested 2026-11-12.** Do not represent this as an existing feature or claim phone measurements were collected.

## User-approved defaults

| Setting | Default |
|---|---|
| Personalized pace learning | **Enabled** (preference; see explicit permission/consent gate below) |
| Planning mode | **Balanced** |
| Extra transfer buffer | **3 minutes** |
| Data storage | On-device only by default |
| Modes | Walking and cycling initially; scooter classification only after validation |

**Privacy distinction:** “learning enabled” is the user's preferred configuration, **not** consent to start collecting sensors or location automatically. First use requires clear explanation, affirmative in-app action and Android runtime permissions where applicable. Allow opting out and manual speeds.

## Problem

A fixed walking radius or universal speed underestimates transfer time for some riders. Estimate walking/cycling travel time from observed, quality-filtered personal movement; incorporate walking-path length, crossings, elevation where authoritative data exists, and uncertainty. The system must not assume that one sprint or GPS spike is a sustainable pace.

## Android architecture

- **Foreground-only MVP:** an explicitly started calibration session or user-initiated journey, with a visible start/stop state. No always-on background monitoring, background location or persistent foreground service in MVP.
- **Signals:** Android `SensorManager` accelerometer and step detector/counter where available, plus `LocationManager`/Fused Location Provider (optional Play Services dependency, not required for fully offline functionality). Activity Recognition Transition API can optionally distinguish walking, cycling and in-vehicle when Google Play Services is available; do not make it an offline prerequisite. Accelerometer alone cannot derive reliable ground speed due to drift and phone orientation.
- **Permissions:** `ACCESS_FINE_LOCATION` or coarse location only as justified by accuracy needs, requested at runtime; `ACTIVITY_RECOGNITION` where used; sensor access and location permission must be independent. Explain device/OS restrictions. Denial must preserve manual transfer planning.
- **Classification:** use user-selected activity during calibration as ground truth; optional activity classifier can suggest mode but must not silently relabel scooter/vehicle travel as walking or cycling. Detect pauses and unrealistic velocity jumps.
- **Measurement:** timestamped positions with accuracy, elapsed realtime, segment distance along credible location points, speed quality and sample count. Use monotonic clock; discard low-accuracy/outlier segments, implausible jumps and stationary samples. Compare GPS displacement with steps where supported; avoid double counting steps as distance. Avoid estimating exact street geometry from sensors.
- **Profile:** locally stored per-mode robust distribution (e.g. weighted median pace, 20th/50th/80th percentiles and confidence) with bounded recency weighting; no raw trajectory retention by default. Minimum sample/distance thresholds before personalization. User can inspect, pause, reset, delete or export aggregate pace profiles.
- **Planner:** consume an offline pedestrian/cycling network when licensed and available; fallback to clearly labeled geometric estimate with conservative detour factor, never describe it as a verified route. Predicted duration = path length / conservative per-mode speed + verified crossing/elevation penalties where available + **180 seconds** configurable transfer buffer. Account for boarding cutoff, platform access and transfer constraints when documented. Balanced mode uses a conservative pace percentile; calibrate percentile based on measured on-time performance, not a fabricated fixed confidence guarantee.
- **Offline:** sensor sampling, profile aggregation, storage and prediction run on device with no network calls. An offline map/path graph and offline transit schedule are separate prerequisites for end-to-end airplane-mode routing. Cloud geocoding and live alerts remain optional.
- **Architecture boundary:** implement a platform-neutral `MobilityProfile` / `TransferEstimate` contract and deterministic algorithm fixtures so iOS and Android can produce equivalent results from the same profile, even if sensor adapters differ.

## Calibration and fallback

1. User explicitly starts a walking calibration on a safe familiar route; optionally repeats for cycling. Do not instruct users to interact with a phone while riding.
2. Show sample quality and minimum distance/time before using personalized estimates. Collect multiple ordinary trips rather than a single best speed.
3. When data are sparse, permissions denied, GPS inaccurate, or activity ambiguous, use clearly labeled editable manual pace and conservative defaults. Never force a sensor session to get directions.
4. Keep the **3-minute additional buffer** on top of estimated connection movement and access time. Avoid adding it twice for nested legs or applying it to in-vehicle transit time.
5. Provide explicit controls for learning on/off, Balanced/Fastest/Extra-cautious, buffer 0–10 minutes, walking/cycling manual speeds, profile reset and local deletion.
6. Recalibrate gradually with ordinary journeys only when user explicitly permits measurement; prevent mode contamination and noisy outliers.

## Privacy and safety

- No third-party analytics or server upload of pace, location history or personal mobility profile by default.
- Data minimization: persist aggregates, sample counts, last calibration date and quality flags, not raw coordinates/traces unless separately and explicitly authorized.
- Explain that motion patterns may reveal sensitive routine information. Protect stored data via app-private storage; avoid logging location coordinates, especially in crash logs.
- Honor Android permissions, battery optimization and lifecycle. Stop sampling when the user stops a session or app loses authorized foreground context.
- Provide accessible alternatives for users with limited mobility, wheelchairs or variable pace. Do not infer disability, health status or fitness from sensor data.
- Conservative routing must distinguish missed-connection risk from guaranteed outcomes. No risky rushing prompts or unsafe crossing suggestions.

## Acceptance tests (synthetic first, device later)

1. Default settings are enabled preference / Balanced / 180-second buffer, but no collection begins before affirmative in-app start and necessary permissions.
2. Denied location and activity permissions leave editable manual transfer speed and route planning functional.
3. Controlled 600 m path with walking speed 1.25 m/s gives movement 480 s plus 180 s buffer = 660 s before other documented penalties.
4. Stationary intervals, poor-accuracy fixes, out-of-order timestamps, GPS jumps, and implausible speed are rejected or explicitly modeled, never silently treated as sustained walking speed.
5. Distinct walking and cycling calibration data remain separated; scooter and motor-vehicle samples cannot contaminate either.
6. Small sample count uses manual/default pace with an uncertainty label; sufficient clean samples produce stable, bounded aggregate profile.
7. A one-off sprint does not materially inflate the robust ordinary walking estimate.
8. Balanced mode and buffer changes deterministically affect feasibility; buffer is applied once per transfer, not once per segment.
9. Overnight schedules, calendar exceptions, last-departure and return feasibility use the same conservative transfer time and official schedule provenance.
10. Airplane-mode unit/integration tests show no network access for profile/prediction; actual device airplane-mode map and journey acceptance remains blocked until those components exist.
11. User can pause learning and delete local profile; no new measurements occur after pause and deletion persists after restart.
12. Tests on real Android hardware verify permission flow, sensor availability variance, app lifecycle, battery impact, accuracy across pocket/bag/hand carry and device rotation. Mark these **not run** until executed.

## Delivery stages and dependencies

- **Phase A (documentation, this PR):** record proposal, defaults, architecture, privacy, calibration and tests.
- **Phase B:** deterministic Kotlin estimator/profile with synthetic tests and editable manual fallback.
- **Phase C:** opt-in Android foreground calibration and local aggregate storage.
- **Phase D:** integrate offline pedestrian graph and source-aware timetable planner; prove transfer and return feasibility in airplane mode.
- **Phase E:** optional activity recognition, cycling refinements, iOS parity, and measured accuracy/battery review.

Do not implement sensor collection, request permissions, or claim device testing as part of this documentation PR.
