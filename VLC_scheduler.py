import configparser
import vlc  # if you do not have vlc module installed please use the command `pip install python-vlc`
import logging
import os
import random
from datetime import datetime
from gui import VLC_GUI

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
