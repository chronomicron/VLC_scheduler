import os
import configparser
import vlc  # if you do not have vlc module installed please use the command `pip install python-vlc`
from datetime import datetime
from gui import VLC_GUI
import random

# Define the path to the settings file
SETTINGS_FILE = 'settings.ini'

def load_settings():
    """
    Load settings from the ini file.

    Returns:
        configparser.ConfigParser: Config object containing the settings.
    """
    config = configparser.ConfigParser()
    
    # Check if the settings file exists
    if os.path.exists(SETTINGS_FILE):
        config.read(SETTINGS_FILE)
        return config
    else:
        raise FileNotFoundError(f"{SETTINGS_FILE} does not exist. Please create it with the necessary settings.")

def initialize_vlc(vlc_path):
    """
    Initialize VLC using its API.

    Args:
        vlc_path (str): Path to the VLC executable.

    Returns:
        vlc.Instance: VLC instance.
    """
    # Create VLC instance with the specified VLC path
    instance = vlc.Instance(vlc_path)
    return instance

if __name__ == "__main__":
    try:
        # Load settings from the settings.ini file
        settings = load_settings()
        
        # Initialize VLC
        vlc_path = settings['Paths']['vlc_path']
        vlc_instance = initialize_vlc(vlc_path)
        
        # Launch the GUI and pass the settings and VLC instance
        app = VLC_GUI(settings, SETTINGS_FILE, vlc_instance)
        app.run()
    except Exception as e:
        print(f"Error: {e}")
