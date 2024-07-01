import os
import sys
import configparser
import logging
import vlc
from gui import VLC_GUI

# Initialize logging
logging.basicConfig(filename='log.txt', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_settings(settings_file):
    """
    Load the settings from the ini file.

    Args:
        settings_file (str): The path to the settings file.

    Returns:
        configparser.ConfigParser: The loaded settings.
    """
    settings = configparser.ConfigParser()
    if os.path.exists(settings_file):
        settings.read(settings_file)
    else:
        logging.error(f"Settings file {settings_file} not found.")
        sys.exit(1)
    return settings

def main():
    """
    Main function to initialize and run the VLC Scheduler.
    """
    settings_file = 'settings.ini'
    settings = load_settings(settings_file)

    vlc_instance = vlc.Instance()

    gui = VLC_GUI(settings, settings_file, vlc_instance)
    logging.info("VLC Scheduler started.")
    gui.run()

if __name__ == "__main__":
    main()
