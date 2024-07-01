"""
If you get the following warning when executing:
main libvlc error: stale plugins cache: modified C:\Program Files\VideoLAN\VLC\plugins\

try doing the following:
- open a prompt, terminal or cmd window, as administrator
- navigate to where VLC is installed and look for a program called vlc-cache-gen.exe
- run or execute the program vlc-cache-gen.exe and pass it the folder where the plugins are stored.
So in Windows, with terminal as admin navigate to VLC and execute the following:
vlc-cache-gen.exe \plugins
this should clear up the warning messages.
"""

import configparser
import vlc  # If you do not have vlc module installed, please use the command `pip install python-vlc`
import logging
from gui import VLC_GUI


# Set up logging to write actions and errors to log.txt
logging.basicConfig(filename='log.txt', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

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
