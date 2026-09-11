"""
gui.py — VLC Scheduler Tkinter admin/monitoring GUI

What this file does:
    Defines VLC_GUI, a Tkinter window that displays and edits the schedule
    from settings.ini, and drives the actual VLC playback (play/pause/stop/
    next/previous/fullscreen). This is the admin-facing control surface —
    day-to-day monitoring is meant to happen via the web interface
    (VLC_scheduler.py), not this window. This GUI is only needed for local
    maintenance on the Raspberry Pi itself.

How it's instantiated:
    Not run directly — VLC_scheduler.py creates it on a background thread:

        vlc_gui_instance = VLC_GUI(config, settings_file, vlc_instance, shared_state)
        vlc_gui_instance.root.mainloop()

    Requires:
        config        - a configparser.ConfigParser() with settings.ini loaded
        settings_file - path to settings.ini, so edits can be written back
        vlc_instance  - a vlc.Instance() (from python-vlc)
        shared_state  - a dict shared with the Flask app for cross-thread status
        gui_ready     - (optional) a threading.Event, set once __init__
                        finishes, so the Flask thread knows it's safe to call
                        into vlc_gui_instance — see VLC_scheduler.py

    Also writes heartbeat.txt (a plain Unix timestamp) every 30s while
    running, so an external watchdog (cron, systemd) can detect a hang and
    restart the app — see plan.md Phase 0.

    Thread safety: Tkinter widgets may only be touched from the thread
    running root.mainloop(). Since VLC_scheduler.py's Flask server runs on
    its own thread, it must not call playback methods (play_media, etc.)
    directly — use run_on_gui_thread(func, *args) instead, which marshals
    the call onto the GUI thread via root.after(0, ...).

Platform:
    Linux (Raspberry Pi / Raspbian). Previously targeted Windows during early
    development (see settings.ini history) — that is no longer the case.
"""

import os
import random
import time
import vlc
import configparser
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from datetime import datetime

class VLC_GUI:
    def __init__(self, config, settings_file, vlc_instance, shared_state, gui_ready=None):
        # Initialize the VLC GUI with configuration, settings file, VLC instance, and shared state
        self.config = config
        self.settings_file = settings_file
        self.vlc_instance = vlc_instance
        self.shared_state = shared_state

        # Optional threading.Event, set once this __init__ finishes building
        # everything below. Lets VLC_scheduler.py's Flask routes check
        # "is the GUI actually ready?" before calling into vlc_gui_instance,
        # instead of racing against GUI construction on a separate thread.
        self.gui_ready = gui_ready

        # Initialize the main Tkinter window
        self.root = tk.Tk()
        self.root.title("VLC Scheduler")

        # Start minimized. This GUI is an admin/maintenance tool only — the
        # end user never interacts with it, and it must never sit on top of
        # (or behind, ambiguously) the fullscreen video output on the TV.
        # Pop it back up yourself (e.g. via VNC) only when doing maintenance.
        self.root.iconify()

        # StringVar to keep track of the currently playing media
        self.currently_playing = tk.StringVar()
        self.currently_playing.set("None")

        self.is_playing = False  # Flag to check if media is playing

        # VLC player instance
        self.player = self.vlc_instance.media_player_new()

        # Create menu bar
        self.create_menu()

        # Create GUI components
        # NOTE: the old "Path to VLC player folder" frame has been removed.
        # It only made sense on Windows, where VLC's install location had to
        # be pointed at manually. On Linux, python-vlc finds the system-
        # installed VLC automatically, so there's nothing to configure here.
        self.create_schedule_frame()
        self.create_controls_frame()
        self.create_currently_playing_label()

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start the heartbeat: proof-of-life for external monitoring (cron
        # job, /status endpoint, etc). Written on a recurring Tkinter timer
        # rather than tied to playback, so it reflects "the app is alive and
        # its event loop is running," not "media happens to be playing."
        self.heartbeat_file = 'heartbeat.txt'
        self.heartbeat_interval_ms = 30000  # 30 seconds
        self.write_heartbeat()

        # Everything above is now fully constructed — safe for other threads
        # (the Flask web server) to start calling into this instance.
        if self.gui_ready is not None:
            self.gui_ready.set()

    def write_heartbeat(self):
        # Write the current Unix timestamp to the heartbeat file, then
        # schedule the next write. A monitoring script (e.g. cron) can check
        # this file's contents' age to detect a hung or crashed app and
        # trigger a restart. Plain epoch integer, not JSON — kept as simple
        # as possible since this is a health signal, not a data payload.
        try:
            with open(self.heartbeat_file, 'w') as f:
                f.write(str(int(time.time())))
        except OSError:
            # Don't let a heartbeat write failure (e.g. disk full, bad
            # permissions) crash the app — if writes keep failing, the file
            # will simply go stale and the external monitor will restart us,
            # which is the correct outcome anyway.
            pass

        self.root.after(self.heartbeat_interval_ms, self.write_heartbeat)

    def run_on_gui_thread(self, func, *args):
        # Tkinter is not thread-safe — widgets (StringVars, labels, etc.)
        # must only be touched from the thread running root.mainloop().
        # Flask, however, runs on its own thread and needs to trigger
        # playback actions (play/pause/stop/...) that touch those widgets.
        #
        # root.after(0, ...) schedules a callback to run on the GUI's own
        # event loop at its next opportunity, which is the standard way to
        # safely hand work from another thread over to Tkinter. Call this
        # instead of calling e.g. self.play_media() directly from Flask.
        self.root.after(0, lambda: func(*args))

    def create_menu(self):
        # Create the menu bar
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        
        controlmenu = tk.Menu(menubar, tearoff=0)
        controlmenu.add_command(label="Reinitialize", command=self.reinitialize_schedules)
        menubar.add_cascade(label="Controls", menu=controlmenu)
        
        self.root.config(menu=menubar)

    def create_schedule_frame(self):
        # Create a frame for the schedule
        # NOTE: this used to be row=1 (below the now-removed VLC path frame).
        # It's row=0 now since that frame is gone.
        #
        # This method gets called more than once at runtime (e.g. whenever
        # /edit_schedule_path is hit), not just at startup. Without
        # destroying the previous frame first, each call used to leave the
        # old LabelFrame and all its child widgets sitting around in memory
        # while a new one was gridded into the same cell on top of it —
        # overlapping/duplicate widgets that got worse with every edit.
        if hasattr(self, 'schedule_frame'):
            self.schedule_frame.destroy()

        self.schedule_frame = tk.LabelFrame(self.root, text="Schedule")
        self.schedule_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        for i, section in enumerate([s for s in self.config.sections() if s.startswith('Schedule_')]):
            start_label = tk.Label(self.schedule_frame, text=f"{section} start time:")
            start_label.grid(row=i, column=0, padx=5, pady=5, sticky="e")

            start_entry = tk.Entry(self.schedule_frame)
            start_entry.insert(0, self.config[section]['start'])
            start_entry.grid(row=i, column=1, padx=5, pady=5)

            stop_label = tk.Label(self.schedule_frame, text=f"{section} stop time:")
            stop_label.grid(row=i, column=2, padx=5, pady=5, sticky="e")

            stop_entry = tk.Entry(self.schedule_frame)
            stop_entry.insert(0, self.config[section]['stop'])
            stop_entry.grid(row=i, column=3, padx=5, pady=5)

            path_label = tk.Label(self.schedule_frame, text=f"{section} path:")
            path_label.grid(row=i, column=4, padx=5, pady=5, sticky="e")

            path_entry = tk.Entry(self.schedule_frame, width=50)
            path_entry.insert(0, self.config[section]['path'])
            path_entry.grid(row=i, column=5, padx=5, pady=5)

            edit_button = tk.Button(self.schedule_frame, text="Edit", command=lambda s=section: self.edit_schedule_path(s))
            edit_button.grid(row=i, column=6, padx=5, pady=5)

    def create_controls_frame(self):
        # Create a frame for the media controls
        # NOTE: row shifted from 2 -> 1 now that the VLC path frame is gone.
        controls_frame = tk.LabelFrame(self.root, text="Controls")
        controls_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        play_button = tk.Button(controls_frame, text="Play", command=self.play_media)
        play_button.grid(row=0, column=0, padx=5, pady=5)

        pause_button = tk.Button(controls_frame, text="Pause", command=self.pause_media)
        pause_button.grid(row=0, column=1, padx=5, pady=5)

        stop_button = tk.Button(controls_frame, text="Stop", command=self.stop_media)
        stop_button.grid(row=0, column=2, padx=5, pady=5)

        next_button = tk.Button(controls_frame, text="Next", command=self.next_media)
        next_button.grid(row=0, column=3, padx=5, pady=5)

        previous_button = tk.Button(controls_frame, text="Previous", command=self.previous_media)
        previous_button.grid(row=0, column=4, padx=5, pady=5)

        fullscreen_button = tk.Button(controls_frame, text="Fullscreen", command=self.toggle_fullscreen)
        fullscreen_button.grid(row=0, column=5, padx=5, pady=5)

    def create_currently_playing_label(self):
        # Create a label to display the currently playing media
        # NOTE: row shifted from 3 -> 2 now that the VLC path frame is gone.
        currently_playing_frame = tk.LabelFrame(self.root, text="Currently Playing")
        currently_playing_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.currently_playing_label = tk.Label(currently_playing_frame, textvariable=self.currently_playing)
        self.currently_playing_label.grid(row=0, column=0, padx=5, pady=5)

    def edit_schedule_path(self, section):
        # Edit the path for a schedule
        path = filedialog.askdirectory()
        if path:
            self.config[section]['path'] = path
            with open(self.settings_file, 'w') as configfile:
                self.config.write(configfile)
            self.shared_state['config'] = self.config
            self.create_schedule_frame()

    def play_media(self):
        # Start playing media based on the schedule
        current_time = datetime.now().time()
        for section in [s for s in self.config.sections() if s.startswith('Schedule_')]:
            start_time = datetime.strptime(self.config[section]['start'], "%H:%M").time()
            stop_time = datetime.strptime(self.config[section]['stop'], "%H:%M").time()
            if start_time <= current_time <= stop_time:
                path = self.config[section]['path']
                playlist_file = os.path.join(path, 'VLC_scheduler.txt')
                if not os.path.exists(playlist_file):
                    self.reinitialize_schedule(path)

                with open(playlist_file, 'r') as f:
                    media_list = f.read().splitlines()

                if not media_list:
                    self.reinitialize_schedule(path)
                    with open(playlist_file, 'r') as f:
                        media_list = f.read().splitlines()

                if media_list:
                    media_file = random.choice(media_list)
                    media_path = os.path.join(path, media_file)
                    self.currently_playing.set(media_file)
                    self.shared_state['currently_playing'] = media_file
                    self.play_media_file(media_path)

                    # Remove the played file from the playlist
                    media_list.remove(media_file)
                    with open(playlist_file, 'w') as f:
                        f.write('\n'.join(media_list))

    def play_media_file(self, media_path):
        # Play the selected media file
        media = self.vlc_instance.media_new(media_path)
        self.player.set_media(media)
        self.player.play()
        self.player.set_fullscreen(True)
        self.player.video_set_key_input(False)
        self.player.video_set_mouse_input(False)
        self.is_playing = True
        self.root.after(1000, self.check_media_end)

    def check_media_end(self):
        # Check if the current media has ended and play the next one if necessary
        if not self.is_playing:
            return

        state = self.player.get_state()
        if state in [vlc.State.Ended, vlc.State.Stopped]:
            self.is_playing = False
            self.play_media()
        else:
            self.root.after(1000, self.check_media_end)

    def pause_media(self):
        # Pause the currently playing media
        self.player.pause()

    def stop_media(self):
        # Stop the currently playing media and reset the playing flag
        self.is_playing = False
        self.player.stop()
        self.currently_playing.set("None")
        self.shared_state['currently_playing'] = "None"

    def next_media(self):
        # Skip to the next media
        self.play_media()

    def previous_media(self):
        # Placeholder for previous media functionality
        pass

    def toggle_fullscreen(self):
        # Toggle fullscreen mode
        is_fullscreen = self.player.get_fullscreen()
        self.player.set_fullscreen(not is_fullscreen)

    def reinitialize_schedules(self):
        # Reinitialize all schedules
        for section in [s for s in self.config.sections() if s.startswith('Schedule_')]:
            path = self.config[section]['path']
            self.reinitialize_schedule(path)

    def reinitialize_schedule(self, path):
        # Reinitialize the schedule for a specific path
        playlist_file = os.path.join(path, 'VLC_scheduler.txt')
        media_files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        with open(playlist_file, 'w') as f:
            f.write('\n'.join(media_files))

    def on_closing(self):
        # Handle the window close event
        self.stop_media()
        self.root.destroy()
        