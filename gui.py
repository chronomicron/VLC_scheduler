# gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import vlc  # Ensure you have installed this package using `pip install python-vlc`
import random
import os
import configparser
from datetime import datetime

class VLC_GUI:
    def __init__(self, config, settings_file, vlc_instance):
        """
        Initialize the VLC_GUI class.
        
        Parameters:
        config (ConfigParser): Configuration parser object for settings.
        settings_file (str): Path to the settings.ini file.
        vlc_instance (vlc.Instance): VLC instance object.
        """
        # Store configuration and VLC instance
        self.config = config
        self.settings_file = settings_file
        self.vlc_instance = vlc_instance

        # Initialize VLC media player
        self.player = vlc_instance.media_player_new()

        # Flag to control continuous playback
        self.is_playing = False

        # Initialize the main window
        self.root = tk.Tk()
        self.root.title("VLC Scheduler")

        # Create menu
        self.create_menu()

        # Create frames
        self.create_frames()

        # Initialize the schedule
        self.update_schedule_display()

    def create_menu(self):
        """Create the menu bar with File and Controls menus."""
        menubar = tk.Menu(self.root)

        # File menu
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        # Controls menu
        controlmenu = tk.Menu(menubar, tearoff=0)
        controlmenu.add_command(label="Reinitialize", command=self.reinitialize)
        menubar.add_cascade(label="Controls", menu=controlmenu)

        self.root.config(menu=menubar)

    def create_frames(self):
        """Create the main frames in the GUI."""
        self.path_frame = ttk.LabelFrame(self.root, text="Path to VLC player folder")
        self.path_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.schedule_frame = ttk.LabelFrame(self.root, text="Schedule")
        self.schedule_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.control_frame = ttk.LabelFrame(self.root, text="Controls")
        self.control_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # VLC path input
        self.vlc_path_var = tk.StringVar()
        self.vlc_path_var.set(self.config['Paths']['vlc_path'])
        self.vlc_path_entry = ttk.Entry(self.path_frame, textvariable=self.vlc_path_var, width=50)
        self.vlc_path_entry.grid(row=0, column=0, padx=5, pady=5)

        self.edit_vlc_path_button = ttk.Button(self.path_frame, text="Edit", command=self.edit_vlc_path)
        self.edit_vlc_path_button.grid(row=0, column=1, padx=5, pady=5)

        # Currently playing label
        self.currently_playing_label = ttk.Label(self.control_frame, text="Currently playing: None")
        self.currently_playing_label.grid(row=0, column=0, columnspan=6, sticky=tk.W, pady=(5, 5))

        # Control buttons
        self.play_button = ttk.Button(self.control_frame, text="Play", command=self.start_continuous_playback)
        self.play_button.grid(row=1, column=0, padx=5, pady=5)

        self.pause_button = ttk.Button(self.control_frame, text="Pause", command=self.pause_media)
        self.pause_button.grid(row=1, column=1, padx=5, pady=5)

        self.stop_button = ttk.Button(self.control_frame, text="Stop", command=self.stop_media)
        self.stop_button.grid(row=1, column=2, padx=5, pady=5)

        self.previous_button = ttk.Button(self.control_frame, text="Previous", command=self.previous_media)
        self.previous_button.grid(row=1, column=3, padx=5, pady=5)

        self.next_button = ttk.Button(self.control_frame, text="Next", command=self.next_media)
        self.next_button.grid(row=1, column=4, padx=5, pady=5)

        self.fullscreen_button = ttk.Button(self.control_frame, text="Fullscreen", command=self.toggle_fullscreen)
        self.fullscreen_button.grid(row=1, column=5, padx=5, pady=5)

    def update_schedule_display(self):
        """Update the schedule display in the GUI."""
        for widget in self.schedule_frame.winfo_children():
            widget.destroy()

        row = 0
        for section in self.config.sections():
            if section.startswith('Schedule_'):
                start_time = self.config[section]['start']
                end_time = self.config[section]['stop']
                path = self.config[section]['path']

                # Display schedule information
                ttk.Label(self.schedule_frame, text=f"{start_time} - {end_time}: {path}").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

                # Add edit button for each schedule
                edit_button = ttk.Button(self.schedule_frame, text="Edit", command=lambda section=section: self.edit_schedule(section))
                edit_button.grid(row=row, column=1, padx=5, pady=5)

                row += 1

    def edit_vlc_path(self):
        """Edit the VLC player path."""
        new_path = filedialog.askdirectory(title="Select VLC Player Folder")
        if new_path:
            self.vlc_path_var.set(new_path)
            self.config['Paths']['vlc_path'] = new_path
            with open(self.settings_file, 'w') as configfile:
                self.config.write(configfile)

    def edit_schedule(self, section):
        """Edit the schedule path."""
        new_path = filedialog.askdirectory(title="Select Folder for Schedule")
        if new_path:
            self.config[section]['path'] = new_path
            with open(self.settings_file, 'w') as configfile:
                self.config.write(configfile)
            self.update_schedule_display()

    def start_continuous_playback(self):
        """Start the continuous playback of media files."""
        self.is_playing = True
        self.play_media()

    def play_media(self):
        """Play media based on the current schedule."""
        if not self.is_playing:
            return

        current_time = datetime.now().strftime("%H:%M")

        for section in self.config.sections():
            if section.startswith('Schedule_'):
                start_time = self.config[section]['start']
                end_time = self.config[section]['stop']

                if start_time <= current_time <= end_time:
                    path = self.config[section]['path']
                    media_file = self.select_random_media(path)

                    if media_file:
                        media = self.vlc_instance.media_new(media_file)
                        self.player.set_media(media)
                        self.player.play()
                        self.player.set_fullscreen(True)
                        self.root.after(1000, lambda: self.update_currently_playing(media_file))
                        break
                    else:
                        messagebox.showerror("Error", f"No media files found in {path}")
                        self.log_action(f"Error: No media files found in {path}")
                        break

        # Schedule to check if the media has ended every second
        self.root.after(1000, self.check_media_end)

    def update_currently_playing(self, media_file):
        """Update the label to show the currently playing media file."""
        self.currently_playing_label.config(text=f"Currently playing: {media_file}")

    def check_media_end(self):
        """Check if the current media has ended and start the next one if necessary."""
        if not self.is_playing:
            return

        if self.player.is_playing():
            self.root.after(1000, self.check_media_end)
        else:
            self.play_media()

    def pause_media(self):
        """Pause the current media."""
        self.player.pause()

    def stop_media(self):
        """Stop the current media and stop the continuous playback."""
        self.is_playing = False
        self.player.stop()

    def next_media(self):
        """Play the next media."""
        self.play_media()

    def previous_media(self):
        """Play the previous media."""
        self.play_media()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode for the media player."""
        self.player.toggle_fullscreen()

    def reinitialize(self):
        """Reinitialize the VLC_scheduler.txt files for all schedules."""
        for section in self.config.sections():
            if section.startswith('Schedule_'):
                path = self.config[section]['path']
                self.create_vlc_scheduler_file(path)

    def create_vlc_scheduler_file(self, path):
        """Create or reinitialize the VLC_scheduler.txt file with the directory contents."""
        media_files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        vlc_scheduler_file = os.path.join(path, "VLC_scheduler.txt")

        with open(vlc_scheduler_file, 'w') as f:
            for file in media_files:
                f.write(file + '\n')

    def select_random_media(self, path):
        """
        Select a random media file from the VLC_scheduler.txt file.
        
        Parameters:
        path (str): Path to the directory containing the VLC_scheduler.txt file.
        
        Returns:
        str: Path to the selected media file.
        """
        vlc_scheduler_file = os.path.join(path, "VLC_scheduler.txt")

        if not os.path.exists(vlc_scheduler_file):
            # Create VLC_scheduler.txt if it doesn't exist
            self.create_vlc_scheduler_file(path)

        with open(vlc_scheduler_file, 'r') as f:
            media_files = f.readlines()

        if media_files:
            # Select a random media file and remove it from the list
            selected_media = random.choice(media_files).strip()
            media_files.remove(selected_media + '\n')

            # Update the VLC_scheduler.txt file
            with open(vlc_scheduler_file, 'w') as f:
                f.writelines(media_files)

            return os.path.join(path, selected_media)
        else:
            # Reinitialize the VLC_scheduler.txt file if empty
            self.create_vlc_scheduler_file(path)
            return self.select_random_media(path)  # Retry after reinitialization

    def log_action(self, message):
        """Log actions and errors to a log file."""
        with open("log.txt", "a") as log_file:
            log_file.write(f"{datetime.now()}: {message}\n")

    def run(self):
        """Run the GUI application."""
        self.root.mainloop()
