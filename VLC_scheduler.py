# VLC_scheduler.py
import vlc  # Ensure you have installed this package using `pip install python-vlc`
import configparser
from gui import VLC_GUI

def main():
    """
    Main function to initialize and start the VLC Scheduler GUI.
    """
    # Load settings from the configuration file
    settings_file = 'settings.ini'
    config = configparser.ConfigParser()
    config.read(settings_file)

    # Initialize VLC instance
    vlc_instance = vlc.Instance()

    # Create and run the GUI application
    app = VLC_GUI(config, settings_file, vlc_instance)
    app.run()

if __name__ == '__main__':
    main()
