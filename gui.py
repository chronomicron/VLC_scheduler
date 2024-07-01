import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import vlc  # if you do not have vlc module installed please use the command `pip install python-vlc`
import configparser
import os
import random
import logging
from datetime import datetime

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
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.populate_main_frame()
        
        # Media control buttons
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=self.main_frame.grid_size()[1], column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.currently_playing_label = ttk.Label(control_frame, text="Currently playing: None")
        self.currently_playing_label.grid(row=0, column=0, columnspan=6, sticky=tk.W, pady=(5, 5))

        ttk.Button(control_frame, text="Play", command=self.play_media).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(control_frame, text="Pause", command=self.pause_media).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(control_frame, text="Stop", command=self.stop_media).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(control_frame, text="Next", command=self.next_media).grid(row=1, column=3, padx=5, pady=5)
        ttk.Button(control_frame, text="Previous", command=self.previous_media).grid(row=1, column=4, padx=5, pady=5)
        ttk.Button(control_frame, text="Full Screen", command=self.toggle_fullscreen).grid(row=1, column=5, padx=5, pady=5)
        
        self.player = None  # VLC media player instance

    def populate_main_frame(self):
        """
        Populate the main frame with settings information and edit buttons.
        """
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        row = 0
        for section in self.settings.sections():
            ttk.Label(self.main_frame, text=f"[{section}]", font=("Helvetica", 12, "bold")).grid(row=row, column=0, sticky=tk.W, pady=(5, 2))
            row += 1
            for key, value in self.settings.items(section):
                ttk.Label(self.main_frame, text=f"{key}: {value}").grid(row=row, column=0, sticky=tk.W)
                if key.endswith("_path"):
                    ttk.Button(self.main_frame, text="Edit", command=lambda k=key, s=section: self.edit_path(s, k)).grid(row=row, column=1, sticky=tk.W)
                if section == 'Schedule':
                    ttk.Button(self.main_frame, text="Edit", command=lambda k=key, s=section: self.edit_schedule_path(s, k)).grid(row=row, column=1, sticky=tk.W)
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
                self.populate_main_frame()
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
                self.populate_main_frame()
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
        """Stop the current media and play the next one in the folder."""
        try:
            if self.player:
                self.player.stop()
                self.play_media()
                logging.info("Playing next media.")
        except Exception as e:
            logging.error(f"Failed to play next media: {e}")
            messagebox.showerror("Error", f"Failed to play next media: {e}")

    def previous_media(self):
        """Stop the current media and play the previous one in the folder."""
        try:
            messagebox.showinfo("Info", "Previous functionality is not implemented yet.")
            logging.info("Previous media functionality not implemented.")
        except Exception as e:
            logging.error(f"Failed to execute previous media functionality: {e}")
            messagebox.showerror("Error", f"Failed to execute previous media functionality: {e}")

    def toggle_fullscreen(self):
        """Toggle the VLC media player between full screen and windowed mode."""
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
            logging.error(f"Failed to toggle full screen: {e}")
            messagebox.showerror("Error", f"Failed to toggle full screen: {e}")

    def run(self):
        """Run the GUI main loop."""
        self.root.mainloop()
