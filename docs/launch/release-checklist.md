# Google Play release-readiness checklist (not complete)

- [ ] Verify Android Studio Gradle sync, build, installation, and startup on real Android hardware.
- [ ] Finish and test offline CT/PVTA data acquisition and source coverage, including service calendar freshness.
- [ ] Implement native offline timetable and journey routing with regression tests.
- [ ] Package licensed offline map data and test airplane-mode map use.
- [ ] Implement and test GPS with runtime permission; request only permissions actually needed.
- [ ] Build and test install/update/rollback of signed, checksum-verified data packs.
- [ ] Handle missing/expired feeds visibly and avoid invented routes or live-arrival claims.
- [ ] Export production adaptive icons, monochrome icon, 512x512 store icon, and 1024x500 feature graphic.
- [ ] Capture actual screenshots of tested app features; no misleading mock screenshots.
- [ ] Create privacy policy and support contact; disclose location and data collection accurately.
- [ ] Complete Google Play Data safety form, content rating, target audience, app access, ads, and store listing fields.
- [ ] Check current target API level, app bundle, signing, and Play testing requirements applicable to the developer account.
- [ ] Run accessibility and crash testing on multiple screen sizes, including no-signal conditions.
- [ ] Sign a release Android App Bundle (AAB), test via internal track, then decide on public rollout.

No publication date is committed. No store account or keys should be stored in Git.
