from flask import Flask, render_template, jsonify, request
import vlc
from gui import VLC_GUI
import configparser
import threading
import tkinter as tk


# Configuration file path
settings_file = 'settings.ini'

# Read the configuration file
config = configparser.ConfigParser()
config.read(settings_file)

# Shared state to be accessed by both GUI and web server
shared_state = {
    'currently_playing': "None"
}

# Create a VLC instance
vlc_instance = vlc.Instance()

# Initialize the Tkinter GUI in a separate thread
def run_gui():
    global vlc_gui_instance
    vlc_gui_instance = VLC_GUI(config, settings_file, vlc_instance, shared_state)
    vlc_gui_instance.root.mainloop()

# Start the GUI thread
gui_thread = threading.Thread(target=run_gui)
gui_thread.start()

# Initialize the Flask app
app = Flask(__name__)

@app.route('/')
def index():
    # Render the main page template
    return render_template('index.html')

@app.route('/status')
def status():
    # Return the current status of the scheduler
    return jsonify(shared_state)

@app.route('/control', methods=['POST'])
def control():
    # Handle media control commands
    command = request.json['command']
    if command == 'play':
        vlc_gui_instance.play_media()
    elif command == 'pause':
        vlc_gui_instance.pause_media()
    elif command == 'stop':
        vlc_gui_instance.stop_media()
    elif command == 'next':
        vlc_gui_instance.next_media()
    elif command == 'previous':
        vlc_gui_instance.previous_media()
    elif command == 'fullscreen':
        vlc_gui_instance.toggle_fullscreen()
    return jsonify({"status": "success"})

@app.route('/edit_path', methods=['POST'])
def edit_path():
    # Handle path editing from the web interface
    new_path = request.json['new_path']
    config['Paths']['vlc'] = new_path
    with open(settings_file, 'w') as configfile:
        config.write(configfile)
    shared_state['config'] = config
    vlc_gui_instance.path_entry.delete(0, tk.END)
    vlc_gui_instance.path_entry.insert(0, new_path)
    return jsonify({"status": "success"})

@app.route('/edit_schedule_path/<section>', methods=['POST'])
def edit_schedule_path(section):
    # Handle schedule path editing from the web interface
    new_path = request.json['new_path']
    config[section]['path'] = new_path
    with open(settings_file, 'w') as configfile:
        config.write(configfile)
    shared_state['config'] = config
    vlc_gui_instance.create_schedule_frame()
    return jsonify({"status": "success"})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
