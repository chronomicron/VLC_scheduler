import configparser
import os
import vlc  # if you do not have vlc module installed please use the command `pip install python-vlc`
import logging
from gui import VLC_GUI

# Configure logging
logging.basicConfig(filename="log.txt", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Settings file
settings_file = 'settings.ini'

# Load settings
config = configparser.ConfigParser()
if os.path.exists(settings_file):
    config.read(settings_file)
else:
    config['Paths'] = {'vlc_path': '/usr/bin/vlc'}
    for i, (start, stop) in enumerate([('08:00', '09:59'), ('10:00', '11:59'), ('12:00', '13:59'), ('14:00', '15:59'), ('16:00', '17:59'), ('18:00', '19:59'), ('20:00', '21:59'), ('22:00', '23:59')], 1):
        config[f'Schedule_{i}'] = {'start': start, 'stop': stop, 'path': f'/path/to/folder_{i}'}
    with open(settings_file, 'w') as configfile:
        config.write(configfile)

# Initialize VLC
vlc_instance = vlc.Instance()

# Start the GUI
app = VLC_GUI(config, settings_file, vlc_instance)
app.root.mainloop()
