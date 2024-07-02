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
