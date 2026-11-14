import SwiftUI
import WebKit

struct ContentView: View {
    @AppStorage("atlasServerURL") private var serverURL = ""
    @State private var draftURL = ""
    @State private var activeURL: URL?
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Group {
                if let url = activeURL {
                    AtlasWebView(url: url)
                        .ignoresSafeArea(edges: .bottom)
                } else {
                    Form {
                        Section("Atlas server") {
                            TextField("https://atlas.example.com", text: $draftURL)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                                .keyboardType(.URL)
                            Button("Connect") { connect() }
                            if let errorMessage {
                                Text(errorMessage).foregroundStyle(.red)
                            }
                        }
                        Section("Getting started") {
                            Text("Start the Python Atlas server on your Mac, then enter its reachable HTTPS address. For local development, use your Mac's LAN address only after enabling a development-only HTTP exception.")
                            Text("127.0.0.1 on an iPhone means the iPhone, not your Mac.")
                            Text("This shell needs the existing Python backend. It does not provide offline routing or native background GPS.")
                        }
                    }
                }
            }
            .navigationTitle("Transit Atlas")
            .toolbar {
                if activeURL != nil {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("Server") {
                            activeURL = nil
                            draftURL = serverURL
                        }
                    }
                }
            }
        }
        .onAppear {
            draftURL = serverURL
            if let url = validated(serverURL) { activeURL = url }
        }
    }

    private func validated(_ value: String) -> URL? {
        guard let components = URLComponents(string: value.trimmingCharacters(in: .whitespacesAndNewlines)),
              let scheme = components.scheme?.lowercased(),
              scheme == "https" || scheme == "http",
              let host = components.host, !host.isEmpty,
              components.user == nil, components.password == nil,
              let url = components.url else { return nil }
        // The release app refuses unencrypted transport.
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
        errorMessage = nil
        activeURL = url
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
