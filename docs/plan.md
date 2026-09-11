# VLC Scheduler — Working Plan

Internal reference only, not end-user documentation. Update as we go: mark items
`[ ]` todo, `[x]` done, `[~]` in progress, `[?]` open question/decision needed.

**Environment:** Raspberry Pi running Raspbian (Linux), connected to a TV.
App must run fully unattended — end user (senior) has zero interaction with it.
You (admin) monitor/control remotely via the web interface. A cron job and/or
systemd watchdog restarts the app if it hangs.

---

## Open decisions (need answers before related phases can finish)

- [?] Does the Tkinter GUI run locally on the Pi (risk of showing on the TV
      output) or is it only ever accessed remotely (VNC/SSH/X-forwarding)?
      Affects whether we need to hide/minimize it or keep it off the TV output
      entirely.
- [?] Heartbeat mechanism: heartbeat file + cron, systemd watchdog, or both?
      (Leaning: both — systemd primary, heartbeat file for visibility/debugging
      and exposed via /status.)
- [?] Auto-start on boot via systemd `enable` — confirm yes/no once systemd
      service is set up.
- [?] Final settings.ini paths for real media library location(s) on the Pi.
- [?] List of TV stream URLs to schedule (format: direct HTTP/HLS m3u8 links).
- [?] YouTube playlist URLs the user will curate personally.

---

## Phase 0 — Resilience foundations

- [ ] Add `[Fallback]` section to settings.ini (local folder, always playable)
- [ ] Define failure hierarchy: scheduled source fails → retry a couple times
      → fall back to `[Fallback]` folder → never a blank/frozen screen
- [ ] Remove all blocking UI from the runtime path (no `messagebox` popups that
      wait for a click — log to file only)
- [ ] Heartbeat: write timestamp to `heartbeat.txt` (or similar) every ~20-30s
- [ ] Expose heartbeat/last-updated time via `/status` endpoint for remote
      monitoring
- [ ] Ensure app is idempotent on restart — always comes back up playing
      something (fallback if nothing else) within a few seconds
- [ ] Decide + implement watchdog mechanism (systemd watchdog and/or cron +
      heartbeat file check script)
- [ ] systemd service file (Restart=on-failure, optional WatchdogSec=)
- [ ] Decide on GUI visibility on the Pi's display (see open decision above)

## Phase 1 — Core stability fixes

- [ ] Fix GUI/Flask startup race (readiness flag before Flask serves control
      routes — currently `vlc_gui_instance` may not exist yet when a request
      comes in)
- [ ] Fix cross-thread calls — marshal Flask-triggered actions onto the GUI
      thread via `root.after(0, ...)` instead of calling directly
- [ ] Add proper `logging` module setup (rotating file handler + console)
- [ ] Add error handling around Flask routes (bad/missing JSON keys, missing
      config sections, missing folders/files)
- [ ] Fix `create_schedule_frame()` — currently rebuilds without destroying
      old widgets first, likely causing duplicate widgets stacking up
- [ ] Review `debug=True` / network binding — should not be exposed with
      Werkzeug debugger on if reachable beyond localhost

## Phase 2 — Multi-source scheduling (local / TV streams / YouTube)

- [ ] Redesign settings.ini schema: `type=local|stream|youtube_playlist` per
      schedule block, plus `[Fallback]` section
- [ ] Migrate existing 8 schedule blocks to Linux paths + new schema
- [ ] Remove/repurpose Windows-only `[Paths] vlc=` key (not needed on Linux —
      python-vlc finds system VLC automatically)
- [ ] Refactor `play_media()` to branch by `type`, with fallback wired in at
      every branch (ties into Phase 0 failure hierarchy)
- [ ] Local-file logic (keep existing random rotation behavior)
- [ ] TV stream logic — direct `media_new(url)` for stream list
- [ ] Integrate `yt-dlp`: resolve single video URLs
- [ ] Integrate `yt-dlp`: enumerate playlist entries
- [ ] Handle expiring YouTube stream URLs — resolve just-in-time, never cache
      long-term
- [ ] Retry-then-fallback behavior per source type (local/stream/youtube each
      need sensible retry counts before giving up to fallback)

## Phase 3 — GUI updates (admin tool for you, not the senior)

- [ ] Type selector (`ttk.Combobox`) per schedule row
- [ ] Swap input widget based on type (folder picker vs. URL/playlist entry)
- [ ] Add/remove schedule block buttons
- [ ] Highlight the currently active schedule block
- [ ] In-GUI log/status panel (scrolling Text widget)
- [ ] Visual cleanup pass (ttk theming, consistent spacing)

## Phase 4 — Web interface (remote monitoring)

- [ ] Reflect schedule type + source in web status view
- [ ] Show current stream/playlist name, not just filename
- [ ] Input validation on edit endpoints (new schema fields)
- [ ] Surface heartbeat/health status ("last updated Xs ago") in web UI

## Phase 5 — Documentation (after everything above is working)

- [ ] README.md
- [ ] INSTALL.md (deps, VLC on Raspbian, systemd service setup, cron setup)
- [ ] HOW_TO_USE.md (for you — adding schedule blocks, monitoring via web)
- [ ] CONFIGURATION.md (full settings.ini schema reference incl. Fallback)
- [ ] Code docstrings pass over gui.py / VLC_scheduler.py
- [ ] CHANGELOG.md

---

## Log of decisions made so far

- End user is a senior, fully passive — no interaction expected at all.
- On any failure, fall back to a default local folder rather than skip/retry
  indefinitely.
- Runs on Raspberry Pi / Raspbian, not Windows — auto-start via systemd, not
  Task Scheduler.
- Cron/systemd watchdog restarts the app if it hangs; heartbeat mechanism
  needed to detect hangs.
  