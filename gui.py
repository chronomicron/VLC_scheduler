import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import vlc  # if you do not have vlc module installed please use the command `pip install python-vlc`
import logging
from datetime import datetime
import os
import random


class VLC_GUI:
    def __init__(self, settings, settings_file, vlc_instance):
        """
        Initialize the VLC_GUI class.

        Args:
            settings (configparser.ConfigParser): The settings loaded from the ini file.
            settings_file (str): The path to the settings file.
            vlc_instance (vlc.Instance): The VLC instance to control media playback.
        """
        self.settings = settings
        self.settings_file = settings_file
        self.vlc_instance = vlc_instance
        self.is_fullscreen = False
        self.current_media_path = None
        
        # Create the main window
        self.root = tk.Tk()
        self.root.title("VLC Scheduler")

        # Create the menu bar
        self.create_menu()

        # Create top frame for VLC path
        self.top_frame = ttk.LabelFrame(self.root, text="Path to VLC Player Folder", padding="10")
        self.top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)

        # Create middle frame for schedule
        self.middle_frame = ttk.LabelFrame(self.root, text="Schedule", padding="10")
        self.middle_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)

        # Create bottom frame for media control buttons
        self.bottom_frame = ttk.LabelFrame(self.root, text="Media Controls", padding="10")
        self.bottom_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)
        
        self.populate_frames()
        
        # Media control buttons
        self.currently_playing_label = ttk.Label(self.bottom_frame, text="Currently playing: None")
        self.currently_playing_label.grid(row=0, column=0, columnspan=6, sticky=tk.W, pady=(5, 5))

        ttk.Button(self.bottom_frame, text="Play", command=self.play_media).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(self.bottom_frame, text="Pause", command=self.pause_media).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(self.bottom_frame, text="Stop", command=self.stop_media).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(self.bottom_frame, text="Next", command=self.next_media).grid(row=1, column=3, padx=5, pady=5)
        ttk.Button(self.bottom_frame, text="Previous", command=self.previous_media).grid(row=1, column=4, padx=5, pady=5)
        ttk.Button(self.bottom_frame, text="Full Screen", command=self.toggle_fullscreen).grid(row=1, column=5, padx=5, pady=5)
        
        self.player = None  # VLC media player instance

    def create_menu(self):
        """
        Create the top menu bar with 'File' and 'Controls' menus.
        """
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        controls_menu = tk.Menu(menubar, tearoff=0)
        controls_menu.add_command(label="Reinitialize", command=self.reinitialize)
        menubar.add_cascade(label="Controls", menu=controls_menu)
        
        self.root.config(menu=menubar)

    def reinitialize(self):
        """
        Placeholder function for reinitializing the application.
        """
        logging.info("Reinitialize called - placeholder function")

    def populate_frames(self):
        """
        Populate the top and middle frames with settings information and edit buttons.
        """
        for widget in self.top_frame.winfo_children():
            widget.destroy()
        for widget in self.middle_frame.winfo_children():
            widget.destroy()
        
        row = 0
        for section in self.settings.sections():
            if section == 'Paths':
                for key, value in self.settings.items(section):
                    if key == "vlc_path":
                        ttk.Label(self.top_frame, text=f"{key.replace('_', ' ').title()}: {value}").grid(row=row, column=0, sticky=tk.W)
                        ttk.Button(self.top_frame, text="Edit", command=lambda k=key, s=section: self.edit_path(s, k)).grid(row=row, column=1, sticky=tk.W)
                        row += 1
            elif section == 'Schedule':
                row = 0
                for key, value in self.settings.items(section):
                    ttk.Label(self.middle_frame, text=f"{key.replace('_', ' ').title()}: {value}").grid(row=row, column=0, sticky=tk.W)
                    ttk.Button(self.middle_frame, text="Edit", command=lambda k=key, s=section: self.edit_schedule_path(s, k)).grid(row=row, column=1, sticky=tk.W)
                    row += 1

    def edit_path(self, section, key):
        """
        Open a file dialog to select a new path and update the settings.

        Args:
            section (str): The section in the settings file.
            key (str): The key in the settings file to be updated.
        """
        try:
            new_path = filedialog.askdirectory(title="Select Folder")
            if new_path:
                self.settings.set(section, key, new_path)
                with open(self.settings_file, 'w') as configfile:
                    self.settings.write(configfile)
                self.populate_frames()
                logging.info(f"Updated path for {key} in section {section} to {new_path}")
        except Exception as e:
            logging.error(f"Failed to edit path for {key} in section {section}: {e}")
            messagebox.showerror("Error", f"Failed to edit path: {e}")

    def edit_schedule_path(self, section, key):
        """
        Open a file dialog to select a new path for a schedule entry and update the settings.

        Args:
            section (str): The section in the settings file.
            key (str): The key in the settings file to be updated.
        """
        try:
            new_path = filedialog.askdirectory(title="Select Folder")
            if new_path:
                times, _ = self.settings.get(section, key).split(',')
                new_value = f"{times},{new_path}"
                self.settings.set(section, key, new_value)
                with open(self.settings_file, 'w') as configfile:
                    self.settings.write(configfile)
                self.populate_frames()
                logging.info(f"Updated schedule path for {key} in section {section} to {new_path}")
        except Exception as e:
            logging.error(f"Failed to edit schedule path for {key} in section {section}: {e}")
            messagebox.showerror("Error", f"Failed to edit schedule path: {e}")

    def play_media(self):
        """
        Play a random media file from the current schedule's paths.
        """
        try:
            current_time = datetime.now().strftime("%H:%M")
            for key, value in self.settings.items('Schedule'):
                times, path = value.split(',')
                start_time, end_time = times.split('-')
                
                if start_time <= current_time <= end_time:
                    media_files = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
                    if media_files:
                        media_file = random.choice(media_files)
                        self.player = self.vlc_instance.media_player_new()
                        media = self.vlc_instance.media_new(media_file)
                        self.player.set_media(media)
                        self.player.play()
                        self.current_media_path = media_file
                        self.currently_playing_label.config(text=f"Currently playing: {media_file}")
                        logging.info(f"Started playing: {media_file}")
                    else:
                        logging.error(f"No media files found in {path}")
                        messagebox.showerror("Error", f"No media files found in {path}")
                    return
            logging.error("No schedule matches the current time.")
            messagebox.showerror("Error", "No schedule matches the current time.")
        except Exception as e:
            logging.error(f"Failed to play media: {e}")
            messagebox.showerror("Error", f"Failed to play media: {e}")

    def pause_media(self):
        """Pause the currently playing media."""
        try:
            if self.player:
                self.player.pause()
                logging.info("Paused media.")
        except Exception as e:
            logging.error(f"Failed to pause media: {e}")
            messagebox.showerror("Error", f"Failed to pause media: {e}")

    def stop_media(self):
        """Stop the currently playing media."""
        try:
            if self.player:
                self.player.stop()
                self.currently_playing_label.config(text="Currently playing: None")
                logging.info("Stopped media.")
        except Exception as e:
            logging.error(f"Failed to stop media: {e}")
            messagebox.showerror("Error", f"Failed to stop media: {e}")

    def next_media(self):
        """Play the next media file in the current schedule's paths."""
        self.stop_media()
        self.play_media()

    def previous_media(self):
        """Replay the previous media file."""
        self.stop_media()
        if self.current_media_path:
            try:
                self.player = self.vlc_instance.media_player_new()
                media = self.vlc_instance.media_new(self.current_media_path)
                self.player.set_media(media)
                self.player.play()
                self.currently_playing_label.config(text=f"Currently playing: {self.current_media_path}")
                logging.info(f"Replaying: {self.current_media_path}")
            except Exception as e:
                logging.error(f"Failed to replay media: {e}")
                messagebox.showerror("Error", f"Failed to replay media: {e}")

    def toggle_fullscreen(self):
        """Toggle the full screen mode of the VLC player."""
        try:
            if self.player:
                if self.is_fullscreen:
                    self.player.set_fullscreen(False)
                    self.is_fullscreen = False
                    logging.info("Exited full screen mode.")
                else:
                    self.player.set_fullscreen(True)
                    self.is_fullscreen = True
                    logging.info("Entered full screen mode.")
        except Exception as e:
            logging.error(f"Failed to toggle full screen mode: {e}")
            messagebox.showerror("Error", f"Failed to toggle full screen mode: {e}")

    def run(self):
        """Run the Tkinter main loop."""
        self.root.mainloop()


if __name__ == "__main__":
    import configparser

    # Configure logging
    logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Read settings from settings.ini
    settings_file = "settings.ini"
    config = configparser.ConfigParser()
    config.read(settings_file)

    # Initialize VLC instance
    vlc_instance = vlc.Instance()

    # Start the GUI
    app = VLC_GUI(config, settings_file, vlc_instance)
    app.run()
