# Stage 3: optional on-device developer workflow

This draft adds `bash termux-dev.sh check` (Python/SQLite/Git check), `test` (synthetic Python pack and CLI tests), `adb-devices`, and `logcat` (transient error-level Android logs). Nothing automatically pairs, connects, saves logs or uploads data.

For wireless debugging, enable **Developer options → Wireless debugging** in Android settings, install Android platform tools in Termux if supported, and use the device's displayed pairing code and address with `adb pair HOST:PORT`, followed by `adb connect HOST:PORT` using the separate debugging endpoint shown by Android. These are **manual** commands; Android versions and Termux packaging vary. Do not paste pairing codes or full logs into chats or public issues. Keep debugging off on untrusted networks.

Android logs may include location, URLs or other sensitive content. The script shows only error-level messages but does not guarantee privacy or app-specific filtering. Review any excerpt before sharing. To focus manually on the app, use `adb shell pidof org.southernnewengland.transitatlas` and then `adb logcat --pid <PID>` where supported. Do not grant extra permissions or disable Android security protections just to debug.

For APK builds, prefer existing GitHub Actions; the local Termux setup is intended for data preparation, Python tests and device triage, not guaranteed Gradle builds. Physical-device ADB and Termux execution are unverified.
