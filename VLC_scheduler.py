import configparser
import vlc  # if you do not have vlc module installed please use the command `pip install python-vlc`
import logging
from datetime import datetime
import os
import random
from gui import VLC_GUI


def setup_logging():
    """
    Set up logging configuration to write logs to 'log.txt'.
    """
    logging.basicConfig(filename='log.txt', level=logging.INFO,
                        format='%(asctime)s:%(levelname)s:%(message)s')


def main():
    """
    Main function to set up and start the VLC Scheduler GUI.
    """
    setup_logging()

    # Read settings
    settings_file = 'settings.ini'
    settings = configparser.ConfigParser()
    settings.read(settings_file)

    # Create VLC instance
    vlc_instance = vlc.Instance()

    # Start GUI
    app = VLC_GUI(settings, settings_file, vlc_instance)
    app.root.mainloop()


if __name__ == "__main__":
    main()
