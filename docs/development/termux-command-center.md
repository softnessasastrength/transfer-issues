# Transit Atlas Termux Command Center

Start in the cloned repository with `bash termux-setup.sh`. Requires Termux Python 3.11+, a real interactive terminal and the stacked Termux Stage 1–3 scripts. This is a **stdlib curses TUI** with no external Python UI packages, network calls on startup, root access, or automatic package installation.

The screen shows local database/catalog readiness and available tools. Use arrows or J/K, Enter to run, R to refresh, Q to quit. Feed imports, the loopback server, and Android logcat require explicit Y confirmation. Live server and logcat occupy the terminal until Ctrl+C. The app never silently downloads feeds or connects ADB. Use `bash termux-setup.sh --list` for noninteractive command discovery. For noninteractive read-only checks, `python3 scripts/termux_tui.py --run doctor`.

First-time preparation still requires `pkg install python git sqlite` and private GitHub authentication. To install offline packs: import feeds, start server, enter `http://127.0.0.1:8000` in the **debug** APK, review selected downloads, approve them, and test planner offline. Only agencies actually present in the imported database appear.

**Limitations:** no device verification yet. Long-running imports may not show progress until a subprocess writes a line; press Ctrl+C to interrupt. Terminal size should be at least 54 columns and 24 rows. Termux may suspend background processes when Android aggressively manages battery; keep it foreground during installation. TUI does not bypass app signing, Android permission prompts or GitHub authentication.
