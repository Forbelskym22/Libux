import subprocess
import os
from modules import utils
from .shared import require_pm2, pick_app

def show_status():
    if not require_pm2():
        return
    os.system("clear")
    utils.print_menu_name("PM2 Status")
    subprocess.run(["pm2", "list"])
    utils.pause()


def start_app():
    if not require_pm2():
        return
    os.system("clear")
    utils.print_menu_name("Start app")
    path = utils.ask_required("App path or name (e.g. /var/www/app.js)")
    if path is None:
        return
    result = subprocess.run(["pm2","start",path], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log(f"App '{path}' started.", "success")
    else:
        utils.log(result.stderr.strip() or "Failed to start app.", "error")
    utils.pause()



def stop_app():
    if not require_pm2():
        return
    app = pick_app("Stop app")
    if app is None:
        return
    result = subprocess.run(["pm2", "stop", app], capture_output=True, text= True)
    if result.returncode == 0:
        utils.log(f"App '{app}' stopped.", "success")
    else:
        utils.log(result.stderr.strip() or "Failed to stop app.", "error")
    utils.pause()

def restart_app():
    if not require_pm2():
        return
    app = pick_app("Restart app")
    if app is None:
        return
    result = subprocess.run(["pm2", "restart", app], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log(f"App '{app}' restarted.", "success")
    else:
        utils.log(result.stderr.strip() or "Failed to restart app.", "error")
    utils.pause()

def delete_app():
    if not require_pm2():
        return
    app = pick_app("Delete app")
    if app is None:
        return
    if utils.choose(["yes", "no"], f"Delete '{app}' from PM2?", "error") != "yes":
        return
    result = subprocess.run(["pm2", "delete", app], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log(f"App '{app}' deleted.", "success")
    else:
        utils.log(result.stderr.strip() or "Failed to delete app.", "error")
    utils.pause()

def view_logs():
    if not require_pm2():
        return
    app = pick_app("View logs")
    if app is None:
        return
    os.system("clear")
    utils.print_menu_name(f"Logs - {app}")
    subprocess.run(["pm2", "logs", app, "--lines", "50", "--nostream"])
    utils.pause()