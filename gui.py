import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import configparser
import vlc  # If you do not have vlc module installed, please use the command `pip install python-vlc`
import random
import os
from datetime import datetime
import logging

# Set up logging to write actions and errors to log.txt
logging.basicConfig(filename='log.txt', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

class VLC_GUI:
    def __init__(self, config, settings_file, vlc_instance):
        """
        Initialize the VLC_GUI class.
        
        Args:
            config (ConfigParser): The configuration parser to read settings from.
            settings_file (str): The path to the settings.ini file.
            vlc_instance (vlc.Instance): The VLC instance.
        """
        self.config = config  # Store the configuration parser
        self.settings_file = settings_file  # Store the settings file path
        self.vlc_instance = vlc_instance  # Store the VLC instance

        # Initialize the Tkinter root window
        self.root = tk.Tk()
        self.root.title("VLC Scheduler")
        
        # Create menu
        self.create_menu()

        # Create and place frames
        self.create_frames()

        # Load the scheduled times and paths from the configuration file
        self.load_schedule()

        # Initialize media player control attributes
        self.player = None  # VLC media player instance
        self.is_fullscreen = False  # Fullscreen toggle status
        self.current_media = None  # Currently playing media file path
        self.continuous_play = False  # Continuous play status
        
        # Initialize and place media control buttons
        self.create_media_controls()

    def create_menu(self):
        """
        Create the menu bar with File and Controls menus.
        """
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        controls_menu = tk.Menu(menubar, tearoff=0)
        controls_menu.add_command(label="Reinitialize", command=self.reinitialize)
        menubar.add_cascade(label="Controls", menu=controls_menu)

    def create_frames(self):
        """
        Create and place the three main frames in the GUI.
        """
        self.top_frame = ttk.LabelFrame(self.root, text="VLC Path", padding="10")
        self.top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.middle_frame = ttk.LabelFrame(self.root, text="Schedule", padding="10")
        self.middle_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        self.bottom_frame = ttk.LabelFrame(self.root, text="Controls", padding="10")
        self.bottom_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    def load_schedule(self):
        """
        Load the scheduled times and paths from the configuration file
        and create corresponding widgets in the GUI.
        """
        vlc_path_label = ttk.Label(self.top_frame, text="Path to VLC player folder:")
        vlc_path_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

        vlc_path = self.config['Paths']['vlc_path']
        self.vlc_path_entry = ttk.Entry(self.top_frame, width=50)
        self.vlc_path_entry.insert(0, vlc_path)
        self.vlc_path_entry.grid(row=0, column=1, padx=(0, 10), sticky="w")

        vlc_path_edit_button = ttk.Button(self.top_frame, text="Edit", command=self.edit_vlc_path)
        vlc_path_edit_button.grid(row=0, column=2, sticky="w")

        row = 0
        for section in self.config.sections():
            if section.startswith('Schedule_'):
                row += 1
                start_label = ttk.Label(self.middle_frame, text=f"Start: {self.config[section]['start']}")
                start_label.grid(row=row, column=0, sticky="w")

                stop_label = ttk.Label(self.middle_frame, text=f"Stop: {self.config[section]['stop']}")
                stop_label.grid(row=row, column=1, sticky="w")

                path_label = ttk.Label(self.middle_frame, text=f"Path: {self.config[section]['path']}")
                path_label.grid(row=row, column=2, sticky="w")

                edit_button = ttk.Button(self.middle_frame, text="Edit", command=lambda s=section: self.edit_schedule_path(s))
                edit_button.grid(row=row, column=3, sticky="w")

    def create_media_controls(self):
        """
        Create and place media control buttons in the GUI.
        """
        self.currently_playing_label = ttk.Label(self.bottom_frame, text="Currently playing: None")
        self.currently_playing_label.grid(row=0, column=0, columnspan=6, sticky="w")

        play_button = ttk.Button(self.bottom_frame, text="Play", command=self.start_continuous_play)
        play_button.grid(row=1, column=0, padx=5, pady=5)

        pause_button = ttk.Button(self.bottom_frame, text="Pause", command=self.pause_media)
        pause_button.grid(row=1, column=1, padx=5, pady=5)

        stop_button = ttk.Button(self.bottom_frame, text="Stop", command=self.stop_continuous_play)
        stop_button.grid(row=1, column=2, padx=5, pady=5)

        previous_button = ttk.Button(self.bottom_frame, text="Previous", command=self.previous_media)
        previous_button.grid(row=1, column=3, padx=5, pady=5)

        next_button = ttk.Button(self.bottom_frame, text="Next", command=self.next_media)
        next_button.grid(row=1, column=4, padx=5, pady=5)

        fullscreen_button = ttk.Button(self.bottom_frame, text="Fullscreen", command=self.toggle_fullscreen)
        fullscreen_button.grid(row=1, column=5, padx=5, pady=5)

    def edit_vlc_path(self):
        """
        Open a file dialog to select the VLC path and update the configuration.
        """
        new_path = filedialog.askdirectory(title="Select VLC Path")
        if new_path:
            self.vlc_path_entry.delete(0, tk.END)
            self.vlc_path_entry.insert(0, new_path)
            self.config.set('Paths', 'vlc_path', new_path)
            with open(self.settings_file, 'w') as configfile:
                self.config.write(configfile)
            logging.info(f"Updated VLC path to: {new_path}")

    def edit_schedule_path(self, section):
        """
        Open a file dialog to select a new media path for the given schedule section.
        
        Args:
            section (str): The schedule section to update.
        """
        new_path = filedialog.askdirectory(title="Select Media Path")
        if new_path:
            self.config.set(section, 'path', new_path)
            with open(self.settings_file, 'w') as configfile:
                self.config.write(configfile)
            self.load_schedule()  # Refresh the schedule display
            logging.info(f"Updated {section} path to: {new_path}")

    def start_continuous_play(self):
        """
        Start continuous play mode where videos are played non-stop based on the schedule.
        """
        self.continuous_play = True
        self.play_media()
        logging.info("Started continuous play mode.")

    def play_media(self):
        """
        Play a random media file from the current schedule based on the current time.
        """
        current_time = datetime.now().strftime("%H:%M")
        for section in self.config.sections():
            if section.startswith('Schedule_'):
                start_time = self.config[section]['start']
                stop_time = self.config[section]['stop']
                if start_time <= current_time <= stop_time:
                    media_path = self.config[section]['path']
                    media_file = self.get_next_media_file(media_path)
                    if media_file:
                        self.current_media = media_file
                        self.currently_playing_label.config(text=f"Currently playing: {media_file}")
                        if self.player is not None:
                            self.player.stop()
                        self.player = self.vlc_instance.media_player_new()
                        self.player.set_media(self.vlc_instance.media_new(media_file))
                        self.player.play()
                        logging.info(f"Playing media: {media_file}")
                        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.on_media_end)
                    else:
                        logging.error(f"No media files found in: {media_path}")
                    return
        logging.error("No valid schedule found for the current time.")

    def get_next_media_file(self, media_path):
        """
        Get the next media file to play from the VLC_scheduler.txt file.
        
        Args:
            media_path (str): The path to the media folder.
        
        Returns:
            str: The path to the next media file to play.
        """
        schedule_file = os.path.join(media_path, 'VLC_scheduler.txt')
        if not os.path.exists(schedule_file):
            self.create_schedule_file(media_path)
        
        with open(schedule_file, 'r') as f:
            media_files = f.readlines()
        
        if not media_files:
            self.create_schedule_file(media_path)
            with open(schedule_file, 'r') as f:
                media_files = f.readlines()

        media_files = [file.strip() for file in media_files if file.strip()]
        if media_files:
            next_file = random.choice(media_files)
            media_files.remove(next_file)
            with open(schedule_file, 'w') as f:
                f.writelines(f"{file}\n" for file in media_files)
            return os.path.join(media_path, next_file)
        return None

    def create_schedule_file(self, media_path):
        """
        Create the VLC_scheduler.txt file in the specified media path with a directory listing.
        
        Args:
            media_path (str): The path to the media folder.
        """
        with open(os.path.join(media_path, 'VLC_scheduler.txt'), 'w') as f:
            for item in os.listdir(media_path):
                if os.path.isfile(os.path.join(media_path, item)):
                    f.write(f"{item}\n")
        logging.info(f"Created VLC_scheduler.txt in {media_path}")

    def on_media_end(self, event):
        """
        Event handler for when a media file ends.
        """
        if self.continuous_play:
            self.play_media()

    def pause_media(self):
        """
        Pause the currently playing media.
        """
        if self.player is not None:
            self.player.pause()
            logging.info("Paused media.")

    def stop_continuous_play(self):
        """
        Stop continuous play mode and the currently playing media.
        """
        if self.player is not None:
            self.player.stop()
        self.continuous_play = False
        self.currently_playing_label.config(text="Currently playing: None")
        logging.info("Stopped continuous play mode.")

    def previous_media(self):
        """
        Play the previous media file (not implemented in this example).
        """
        pass

    def next_media(self):
        """
        Play the next media file.
        """
        self.play_media()

    def toggle_fullscreen(self):
        """
        Toggle fullscreen mode for the VLC player.
        """
        if self.player is not None:
            self.is_fullscreen = not self.is_fullscreen
            self.player.toggle_fullscreen()
            logging.info(f"Toggled fullscreen mode: {self.is_fullscreen}")

    def reinitialize(self):
        """
        Reinitialize by reading the settings.ini file and creating VLC_scheduler.txt files
        in each schedule path with the directory listing.
        """
        for section in self.config.sections():
            if section.startswith('Schedule_'):
                path = self.config[section]['path']
                if os.path.exists(path):
                    self.create_schedule_file(path)
                else:
                    logging.error(f"Path does not exist: {path}")

    def run(self):
        """
        Start the Tkinter main loop.
        """
        self.root.mainloop()

if __name__ == "__main__":
    # Load configuration from settings.ini
    config = configparser.ConfigParser()
    settings_file = 'settings.ini'
    config.read(settings_file)

    # Create a VLC instance
    vlc_instance = vlc.Instance()

    # Create and run the GUI application
    app = VLC_GUI(config, settings_file, vlc_instance)
    app.run()
