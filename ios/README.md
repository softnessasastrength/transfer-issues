# Transit Atlas iOS starter (SwiftUI + WKWebView)

This is a **source skeleton**, not a built/tested iOS app. It preserves the current Python/SQLite backend and embeds the existing web interface. No data or server credentials are bundled.

## Build on Mac mini

1. Install Xcode from the Mac App Store and open it once to accept license/install components. Verify `xcodebuild -version`.
2. Install [XcodeGen](https://github.com/yonaskolb/XcodeGen) with `brew install xcodegen` (install Homebrew first if needed).
3. In this repo: `cd ios && xcodegen generate && open TransitAtlas.xcodeproj`.
4. Select the TransitAtlas target, set your own unique bundle identifier under Signing & Capabilities, select your Apple development team, then choose an iPhone simulator or connected iPhone and Run.
5. Enter an **HTTPS** URL for a deployed Atlas backend in the app. The existing `127.0.0.1:8000` Termux URL only works on the phone running that server; it does not point to your Mac.

## Mac-hosted local development

The current Python server defaults to loopback. For an iPhone to connect on the same trusted Wi-Fi, start it explicitly on a LAN interface:

```bash
# Run from the repository root, after data/atlas.sqlite has been created:
python3 server.py --host 0.0.0.0 --port 8000
```

**Warning:** This exposes the development server to other devices on the network. Use only a trusted private network and stop it afterward. Do not forward port 8000 or expose it to the internet. The production app should use authenticated HTTPS hosting.

**HTTP testing caveat:** iOS App Transport Security may block plain HTTP even on a LAN. The generated target enables `NSAllowsLocalNetworking`, which may permit local-network HTTP depending on the URL/OS; it does not guarantee an IP-literal HTTP connection. For reliable testing, use an HTTPS endpoint with a trusted certificate, or temporarily configure a debug-only ATS exception in Xcode. Never ship broad `NSAllowsArbitraryLoads` in Release. The source currently accepts HTTP only in Debug.

**GPS caveat:** Browser geolocation in WKWebView may require additional native permission handling, and insecure HTTP origins are not trustworthy contexts for web geolocation. This skeleton does not claim GPS works on iOS. Native Core Location bridging is a separate milestone.

## Scope / limitations

- Requires a reachable, running Atlas Python API server.
- No bundled SQLite, no offline routing, no background positioning, no native notifications.
- Existing Leaflet, browser-local journal, and all-routes UI are reused.
- Browser persistence in WKWebView is separate from Chrome/Safari. Export personal data from the old browser before migrating.
- Test signing, network privacy prompts, ATS, WebKit permissions, and actual device layout before calling the app operational.
- No App Store submission configuration or production security hardening is included.

The Xcode project is generated locally from `project.yml`, so no generated `.xcodeproj` or signing credentials are committed.
