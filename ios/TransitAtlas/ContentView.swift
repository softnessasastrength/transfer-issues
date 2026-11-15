import SwiftUI
import WebKit

private enum MetroPalette {
    static let background = Color(red: 0.055, green: 0.063, blue: 0.09)
    static let cyan = Color(red: 0.0, green: 0.64, blue: 0.84)
    static let blue = Color(red: 0.16, green: 0.36, blue: 0.75)
    static let orange = Color(red: 0.91, green: 0.38, blue: 0.16)
    static let violet = Color(red: 0.43, green: 0.29, blue: 0.69)
}

private enum MetroPage: String, CaseIterable {
    case start = "start"
    case atlas = "atlas"
    case settings = "settings"
}

struct ContentView: View {
    @AppStorage("atlasServerURL") private var serverURL = ""
    @State private var draftURL = ""
    @State private var activeURL: URL?
    @State private var errorMessage: String?
    @State private var page: MetroPage = .start

    var body: some View {
        ZStack {
            MetroPalette.background.ignoresSafeArea()
            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    Text("PERCIVAL").font(.caption.weight(.semibold)).tracking(3)
                    Spacer()
                    Text("TRANSIT ATLAS").font(.caption2).tracking(1.5)
                }
                .foregroundStyle(.white.opacity(0.7))
                .padding(.horizontal, 22)
                .padding(.top, 16)

                HStack(spacing: 24) {
                    ForEach(MetroPage.allCases, id: \.self) { item in
                        Button {
                            withAnimation(.easeInOut(duration: 0.2)) { page = item }
                        } label: {
                            Text(item.rawValue)
                                .font(.title3.weight(page == item ? .bold : .regular))
                                .foregroundStyle(page == item ? .white : .white.opacity(0.48))
                        }
                        .accessibilityAddTraits(page == item ? .isSelected : [])
                    }
                }
                .padding(.horizontal, 22)
                .padding(.top, 28)
                .padding(.bottom, 16)

                Group {
                    switch page {
                    case .start: startPage
                    case .atlas: atlasPage
                    case .settings: settingsPage
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            }
        }
        .preferredColorScheme(.dark)
        .onAppear {
            draftURL = serverURL
            activeURL = validated(serverURL)
        }
    }

    private var startPage: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                Text("your city.\nyour way.")
                    .font(.system(size: 46, weight: .light, design: .default))
                    .tracking(-1.5)
                    .foregroundStyle(.white)
                    .minimumScaleFactor(0.75)
                    .padding(.bottom, 8)

                GeometryReader { geometry in
                    let tile = (geometry.size.width - 10) / 2
                    VStack(spacing: 10) {
                        HStack(spacing: 10) {
                            metroTile("explore", subtitle: "regional atlas", icon: "map.fill",
                                      color: MetroPalette.cyan, width: tile, height: tile) {
                                page = .atlas
                            }
                            VStack(spacing: 10) {
                                metroTile("connect", subtitle: "atlas server", icon: "network",
                                          color: MetroPalette.blue, width: tile, height: (tile - 10) / 2) {
                                    page = .settings
                                }
                                metroTile("coverage", subtitle: "verify sources", icon: "checkmark.shield",
                                          color: MetroPalette.violet, width: tile, height: (tile - 10) / 2) {
                                    page = .atlas
                                }
                            }
                        }
                        metroTile("plan a journey", subtitle: "outbound + return feasibility",
                                  icon: "arrow.left.arrow.right", color: MetroPalette.orange,
                                  width: geometry.size.width, height: 110) {
                            page = .atlas
                        }
                    }
                }
                .frame(height: ((UIScreen.main.bounds.width - 54 - 10) / 2) + 120)

                HStack(spacing: 8) {
                    Circle()
                        .fill(activeURL == nil ? Color.orange : Color.green)
                        .frame(width: 8, height: 8)
                    Text(activeURL == nil ? "No atlas server configured" : "Atlas server configured; connectivity unverified")
                        .font(.footnote)
                        .foregroundStyle(.white.opacity(0.75))
                }
                Text("Experimental iOS client · no verified offline routing")
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.55))
            }
            .padding(.horizontal, 22)
            .padding(.bottom, 30)
        }
    }

    private func metroTile(_ title: String, subtitle: String, icon: String,
                           color: Color, width: CGFloat, height: CGFloat,
                           action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 30, weight: .light))
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .center)
                Text(title).font(.headline).lineLimit(1)
                Text(subtitle).font(.caption2).lineLimit(2)
            }
            .foregroundStyle(.white)
            .padding(14)
            .frame(width: width, height: height, alignment: .leading)
            .background(color)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(title), \(subtitle)")
    }

    private var atlasPage: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("explore")
                .font(.system(size: 42, weight: .light))
                .foregroundStyle(.white)
                .padding(.horizontal, 22)
            if let url = activeURL {
                AtlasWebView(url: url)
                    .background(.white)
            } else {
                ContentUnavailableView {
                    Label("Atlas unavailable", systemImage: "wifi.slash")
                } description: {
                    Text("Configure a reachable server to open the existing atlas. No timetable or journey is fabricated.")
                } actions: {
                    Button("Configure server") { page = .settings }
                        .buttonStyle(.borderedProminent)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    private var settingsPage: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                Text("settings")
                    .font(.system(size: 42, weight: .light))
                Text("atlas server").font(.title2.weight(.light))
                TextField("https://atlas.example.com", text: $draftURL)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .keyboardType(.URL)
                    .textContentType(.URL)
                    .padding(14)
                    .background(.white.opacity(0.12))
                    .accessibilityLabel("Atlas server URL")
                Button("connect") { connect() }
                    .font(.title3)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(16)
                    .background(MetroPalette.cyan)
                    .foregroundStyle(.white)
                if let errorMessage {
                    Text(errorMessage).foregroundStyle(.orange)
                }
                Text("Use a reachable HTTPS endpoint. In Debug builds only, HTTP may be accepted, subject to iOS App Transport Security. 127.0.0.1 on an iPhone is the phone itself, not your Mac.")
                    .font(.footnote)
                    .foregroundStyle(.white.opacity(0.7))
                Text("The current shell needs the Python backend. Native offline routing, live arrivals and device GPS are not yet verified.")
                    .font(.footnote)
                    .foregroundStyle(.white.opacity(0.7))
            }
            .foregroundStyle(.white)
            .padding(22)
        }
    }

    private func validated(_ value: String) -> URL? {
        guard let components = URLComponents(string: value.trimmingCharacters(in: .whitespacesAndNewlines)),
              let scheme = components.scheme?.lowercased(),
              scheme == "https" || scheme == "http",
              let host = components.host, !host.isEmpty,
              components.user == nil, components.password == nil,
              let url = components.url else { return nil }
        #if !DEBUG
        guard scheme == "https" else { return nil }
        #endif
        return url
    }

    private func connect() {
        guard let url = validated(draftURL) else {
            errorMessage = "Enter a valid HTTPS URL (HTTP is development-only)."
            return
        }
        serverURL = url.absoluteString
        activeURL = url
        errorMessage = nil
        page = .atlas
    }
}

struct AtlasWebView: UIViewRepresentable {
    let url: URL

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.defaultWebpagePreferences.allowsContentJavaScript = true
        let view = WKWebView(frame: .zero, configuration: config)
        view.navigationDelegate = context.coordinator
        view.allowsBackForwardNavigationGestures = true
        view.load(URLRequest(url: url))
        return view
    }

    func updateUIView(_ view: WKWebView, context: Context) {
        if view.url?.absoluteString != url.absoluteString {
            view.load(URLRequest(url: url))
        }
    }

    func makeCoordinator() -> Coordinator { Coordinator() }

    final class Coordinator: NSObject, WKNavigationDelegate {
        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            print("Transit Atlas connection error: \(error.localizedDescription)")
        }
    }
}
