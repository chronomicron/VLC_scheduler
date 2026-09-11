#!/bin/bash
#
# watchdog.sh — VLC Scheduler heartbeat watchdog
#
# What this script does:
#   Checks the age of heartbeat.txt (written every ~30s by gui.py while the
#   app is healthy). If the vlc-scheduler systemd service isn't active, or
#   its heartbeat file is missing/corrupt/older than MAX_AGE_SECONDS (meaning
#   the app is hung even though the process is still alive), this script
#   tells systemd to start or restart it.
#
#   NOTE: this script defers all actual process management to systemd
#   (via `systemctl start/restart vlc-scheduler.service`) rather than
#   spawning/killing the Python process directly. Requires
#   vlc-scheduler.service to already be installed (see that file's header)
#   — this script only handles the "hang" case systemd can't see on its own;
#   systemd's own Restart=on-failure already covers outright crashes.
#
# How it's used:
#   Not run manually day-to-day — installed as a cron job that runs this
#   check on a schedule (every minute is a reasonable starting point, giving
#   a worst case of roughly one minute before recovery).
#
#   1. Edit the CONFIGURATION section below (paths, timeouts) for your setup.
#   2. Make the script executable (one-time):
#        sudo chmod +x /home/pi/vlc_scheduler/watchdog.sh
#   3. Add the cron job to ROOT's crontab, not the pi user's — `systemctl
#      restart` requires root privileges, and this avoids needing sudoers
#      changes just for cron:
#        sudo crontab -e
#      Then add this line (runs every minute, logs to watchdog.log):
#        * * * * * /home/pi/vlc_scheduler/watchdog.sh >> /home/pi/vlc_scheduler/watchdog.log 2>&1
#      Save and exit — cron picks up the new entry automatically, no restart
#      needed.
#   Alternative one-liner that adds the same cron line without opening an
#   editor (safe to re-run — it won't duplicate the line if it's already
#   there):
#        (sudo crontab -l 2>/dev/null | grep -F 'watchdog.sh' || \
#          (sudo crontab -l 2>/dev/null; echo '* * * * * /home/pi/vlc_scheduler/watchdog.sh >> /home/pi/vlc_scheduler/watchdog.log 2>&1')) | sudo crontab -
#
# Platform:
#   Linux (Raspberry Pi / Raspbian), assumes vlc-scheduler.service is already
#   installed via systemd (see vlc-scheduler.service's header for setup).

# ----------------------------- CONFIGURATION --------------------------------
PROJECT_DIR="/home/pi/vlc_scheduler"
HEARTBEAT_FILE="$PROJECT_DIR/heartbeat.txt"
MAX_AGE_SECONDS=90          # allow one missed 30s heartbeat write before acting
SERVICE_NAME="vlc-scheduler.service"
# ------------------------------------------------------------------------


start_service() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting $SERVICE_NAME"
    systemctl start "$SERVICE_NAME"
}

restart_service() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Restarting $SERVICE_NAME (stale/hung)"
    systemctl restart "$SERVICE_NAME"
}


# Is the service even active?
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $SERVICE_NAME not active"
    start_service
    exit 0
fi

# Service is active — is its heartbeat missing or stale?
if [ ! -f "$HEARTBEAT_FILE" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Heartbeat file missing while service is active"
    restart_service
    exit 0
fi

heartbeat_time=$(cat "$HEARTBEAT_FILE" 2>/dev/null)
current_time=$(date +%s)

# If the file's contents aren't a valid number (corrupted write, etc.),
# treat it the same as stale rather than letting the script fail silently.
if ! [[ "$heartbeat_time" =~ ^[0-9]+$ ]]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Heartbeat file unreadable/corrupt"
    restart_service
    exit 0
fi

age=$((current_time - heartbeat_time))

if [ "$age" -gt "$MAX_AGE_SECONDS" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Heartbeat stale (${age}s old, limit ${MAX_AGE_SECONDS}s)"
    restart_service
fi

# Healthy — say nothing, so watchdog.log only fills up when something
# actually happened (start/restart), not every single minute.
