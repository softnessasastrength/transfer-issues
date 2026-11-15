# Transit Atlas KaiOS browser prototype

Open `kaios/index.html` in a desktop browser; resize viewport to 240×320. On Crostini/Linux, from repository root run `python3 -m http.server 8765 --directory kaios --bind 127.0.0.1` and visit http://127.0.0.1:8765. No dependencies, backend changes, device installation, or network requests.

Keys: Up/Down selects; Enter opens; Backspace/Escape returns home; 1–5 shortcuts from home; SoftLeft/SoftRight are provisional and require real B300V keycode verification.

This stage is a **navigation shell**, not a complete departures/journey app. It deliberately does not pretend a cached schedule is live, connect to an unauthenticated backend remotely, or claim offline routing. The storage API is exposed for fixture development, but no sync UI exists. Hardware support, KaiOS browser execution and app packaging are untested. See docs/kaios/FEASIBILITY.md on the separate documentation PR #50.
