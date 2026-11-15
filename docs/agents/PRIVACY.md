# Privacy requirements for all agents

Read `docs/features/privacy-first-journey-verification.md` before editing location, history, motion sensors, telemetry, persistence, crash reporting, exports or store listing claims.

Privacy is a product acceptance criterion, not optional polish. Offline and local-first by default; manual history without location permissions; separate explicit opt-ins for pace learning, journey verification and detailed GPS recording; minimize raw retention; user-controlled deletion/export; never silently upload sensitive records.

Do not commit personal location traces, user histories, debug logs containing coordinates, or real sensor dumps. Use synthetic fixtures. Record any proposed new data collection, permission, SDK, retention period or network transmission in a PR privacy impact note and seek authorization before implementation. Never call sensor proximity proof of vehicle boarding.
