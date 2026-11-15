# Lumia 640 XL: legacy Windows Phone development toolchains

Status: **research and setup guide only** (2026-11-15). No physical Lumia deployment, emulator boot, SDK installation, or application build has been verified. This is an experimental client target; it does not supersede the atlas core roadmap.

## First decide which OS is on the phone

The Lumia 640 XL originally shipped with Windows Phone 8.1; some units were upgraded to **Windows 10 Mobile**. Check **Settings → System → About** on the actual device and record OS build, model/variant, available storage and developer-mode options. A Windows Phone 8.1 application and a Windows 10 UWP application are **not interchangeable targets**.

| Goal | Host | Toolchain | Caveat |
|---|---|---|---|
| Experiment with Windows Phone 8.1 apps | Windows 8.1 | Visual Studio 2013 Update 2+ with Phone 8.1 tools, or VS 2015 with Phone 8.1 tools | Best match for a period-correct Windows 8.1 workstation |
| Run Phone 8.1 emulator | Windows 8.1 **x64 Pro or higher** | Client Hyper-V, CPU SLAT and virtualization enabled | A Windows 8.1 VM may not support nested virtualization; physical-phone testing is an alternative |
| Build Windows 10 Mobile UWP client | Prefer Windows 10 host | VS 2015/2017 with compatible Windows 10 SDK and Mobile tooling | VS 2017 is Microsoft's legacy compatibility recommendation; check component availability |
| Run Windows 10 Mobile client on Lumia | Actual Windows 10 Mobile device | Developer mode, compatible SDK, deploy/debug tools | Physical device deployment is unverified |

Microsoft documents VS 2013 support for Phone 8.1 on Windows 8.1; the emulators require x64 Pro+, Hyper-V and SLAT. Windows 10 UWP binaries cannot run on Windows Phone 8.1. VS 2022/2026 are **not** substitutes for the old Mobile toolchains.

## Windows 8.1 workshop setup

1. Use a **legitimately licensed** Windows 8.1 installation, preferably x64 Pro if emulator work is intended. Keep it isolated from sensitive accounts and untrusted browsing: Windows 8.1 and these IDEs are out of support.
2. Snapshot or image the clean OS. Reserve ample disk space for Visual Studio, SDKs, emulator VHDs and snapshots; avoid assuming historical minimum requirements are comfortable.
3. Install **Visual Studio 2013 Update 2 or later** with Windows Phone 8.1 tools, or the appropriate VS 2015 edition and optional Phone 8.1 components. Archived installers may depend on services no longer online. Prefer Microsoft's official archive; do not assume an old web installer can still download all payloads.
4. If using an emulator, confirm BIOS virtualization, SLAT, Windows edition and Hyper-V. In a VM, explicitly verify nested virtualization support; otherwise target a physical device.
5. Optionally install the **Windows Phone 8.1 Update and Emulators** package. Microsoft's archive includes an ISO option; preserve installers and hashes, and check authenticity before running.
6. Create a minimal Phone 8.1 project with a text label, build it, and record compiler/SDK version and output. Do **not** call the environment working until a build succeeds.
7. For device deployment, verify the phone's OS, unlock/developer registration path and USB drivers first. Historic Microsoft registration services may no longer work; do not promise sideloading until tested.

### Windows 10 Mobile track

Use a **separate Windows 10 VM or workstation** for a compatible Visual Studio 2017 + Windows 10 SDK/UWP toolchain. First build a minimal ARM-targeted UWP application and validate package deployment on the actual Lumia. Confirm the exact SDK minimum/target versions and API contracts against the phone's reported OS build. Avoid claiming that the Windows 8.1 host is a supported Windows 10 Mobile emulator environment.

## Percival architecture and resource contract

- **Client:** native Metro-like XAML UI, touch-first route/stop explorer, small API responses and durable offline snapshots.
- **Core:** existing Python/SQLite atlas remains authoritative for source provenance, verified timetables and routing. Do not duplicate or invent routes to make a demo appear functional.
- **Offline:** downloaded, user-selected coverage and verified map data with license review; cached schedules display validity and freshness. An unavailable feed is **unknown**, not proof of no service.
- **Network:** design for intermittent LTE, older TLS/certificate limitations and no network. Never disable certificate validation or expose the development HTTP server publicly as a workaround.
- **Hardware:** 1 GB physical RAM and 1280×720 display; an app-memory target under 150 MB and cold-start under 3 seconds are **aspirational benchmarks**, not tested limits.
- **Return-home rule:** do not present an outing as feasible until both outbound and return constraints have been checked with known data. Unsupported coverage must be labeled.
- **Compatibility:** treat Lumia hardware as a research target. No claim of deployed, usable, offline, or LTE-tested Percival.

## Reproducible acceptance checklist

- [ ] Identify Lumia model/OS build and developer access.
- [ ] Record Windows host version/edition and whether bare metal or VM.
- [ ] Archive installer names, versions, official URLs, SHA-256 checksums and license provenance locally (no installer binaries in Git).
- [ ] Create/build minimal Phone 8.1 application on Windows 8.1.
- [ ] Separately create/build minimal Windows 10 Mobile ARM UWP app on a compatible host.
- [ ] Verify actual device deployment and restart.
- [ ] Measure cold-start, peak memory, offline behavior, LTE and TLS compatibility.
- [ ] Validate a real source-linked stop/timetable query and an outbound-plus-return journey; fail explicitly on missing data.

## Primary references

- [Microsoft: Visual Studio 2013 system requirements](https://learn.microsoft.com/en-us/visualstudio/releases/2013/vs2013-sysrequirements-vs)
- [Microsoft: Visual Studio 2013 compatibility](https://learn.microsoft.com/en-us/visualstudio/releases/2013/vs2013-compatibility-vs)
- [Microsoft: Windows SDK archive](https://github.com/MicrosoftDocs/windows-dev-docs/blob/docs/hub/apps/windows-sdk/downloads-archive.md)
- [Microsoft: Windows Phone 8.1 emulators](https://www.microsoft.com/en-us/download/details.aspx?id=44574)
- [Microsoft: Windows Phone 8.1 Update and emulators](https://www.microsoft.com/en-ph/download/details.aspx?id=43719)
- [Microsoft: Visual Studio 2022 compatibility (legacy Phone toolchain guidance)](https://learn.microsoft.com/en-us/visualstudio/releases/2022/compatibility)
- [Microsoft: UWP version selection](https://learn.microsoft.com/en-us/windows/uwp/updates-and-versions/choose-a-uwp-version)

## Next implementation decision

This document authorizes no client implementation. After the physical Lumia's OS build and working toolchain are established, propose a tiny proof-of-life app and a separate, reviewable milestone; do not merge or claim completion prematurely.
