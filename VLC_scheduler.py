"""
VLC_scheduler.py — VLC Scheduler entry point / web server

What this file does:
    The main entry point for the app. Starts the Tkinter admin GUI (gui.py)
    on a background thread, then runs a Flask web server on the main thread
    exposing status and playback controls for remote monitoring — this is
    the primary way you (the admin) check on and control the scheduler
    day-to-day, without needing to touch the Pi or the GUI directly.

How it's run:
    From the project folder, on the Raspberry Pi (or any Linux machine with
    VLC + the dependencies installed):

        python3 VLC_scheduler.py

    Then visit http://<pi-ip-address>:5000/ in a browser to monitor/control
    it remotely, or http://127.0.0.1:5000/ if browsing from the Pi itself.

    Requires: flask, python-vlc, VLC itself installed on the system, and a
    settings.ini file in the same folder (see settings.ini's own header for
    its schema).

    A threading.Event (gui_ready) guards against the Flask routes below
    being hit before the GUI thread has finished starting up — see gui.py.

Platform:
    Linux (Raspberry Pi / Raspbian).
"""

from flask import Flask, render_template, jsonify, request
import vlc
from gui import VLC_GUI
import configparser
import threading


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

# Set once the GUI thread has fully finished constructing vlc_gui_instance.
# The Flask routes below check this before touching vlc_gui_instance, so a
# request arriving during startup gets a clear "not ready yet" response
# instead of a NameError/crash from hitting an instance that doesn't exist
# yet.
gui_ready = threading.Event()

# Initialize the Tkinter GUI in a separate thread
def run_gui():
    global vlc_gui_instance
    vlc_gui_instance = VLC_GUI(config, settings_file, vlc_instance, shared_state, gui_ready)
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
    if not gui_ready.is_set():
        return jsonify({"status": "error", "message": "GUI is still starting up, try again in a moment"}), 503
    command = request.json['command']
    # Each of these is marshaled onto the GUI thread via run_on_gui_thread()
    # rather than called directly — Flask runs on its own thread, and these
    # methods touch Tkinter widgets, which isn't thread-safe otherwise.
    if command == 'play':
        vlc_gui_instance.run_on_gui_thread(vlc_gui_instance.play_media)
    elif command == 'pause':
        vlc_gui_instance.run_on_gui_thread(vlc_gui_instance.pause_media)
    elif command == 'stop':
        vlc_gui_instance.run_on_gui_thread(vlc_gui_instance.stop_media)
    elif command == 'next':
        vlc_gui_instance.run_on_gui_thread(vlc_gui_instance.next_media)
    elif command == 'previous':
        vlc_gui_instance.run_on_gui_thread(vlc_gui_instance.previous_media)
    elif command == 'fullscreen':
        vlc_gui_instance.run_on_gui_thread(vlc_gui_instance.toggle_fullscreen)
    return jsonify({"status": "success"})

@app.route('/edit_schedule_path/<section>', methods=['POST'])
def edit_schedule_path(section):
    # Handle schedule path editing from the web interface
    if not gui_ready.is_set():
        return jsonify({"status": "error", "message": "GUI is still starting up, try again in a moment"}), 503
    new_path = request.json['new_path']
    config[section]['path'] = new_path
    with open(settings_file, 'w') as configfile:
        config.write(configfile)
    shared_state['config'] = config
    vlc_gui_instance.run_on_gui_thread(vlc_gui_instance.create_schedule_frame)
    return jsonify({"status": "success"})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
    