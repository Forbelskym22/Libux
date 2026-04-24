import os
import subprocess
from modules import utils
from .shared import require_pm2


def setup_startup():
    if not require_pm2():
        return
    os.system("clear")
    utils.print_menu_name("Setup startup")
    utils.log("Running pm2 startup...", "info")
    subprocess.run(["pm2", "startup"])
    utils.log("Running pm2 save...", "info")
    result = subprocess.run(["pm2", "save"], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log("Startup configured and process list saved.", "success")
    else:
        utils.log(result.stderr.strip() or "pm2 save failed.", "error")
    utils.pause()


def list_ecosystem():
    if not require_pm2():
        return
    os.system("clear")
    utils.print_menu_name("PM2 Configuration")
    subprocess.run(["pm2", "prettylist"])
    utils.pause()


def save_ecosystem():
    if not require_pm2():
        return
    os.system("clear")
    utils.print_menu_name("Save ecosystem")
    result = subprocess.run(["pm2", "save"], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log("PM2 process list saved.", "success")
    else:
        utils.log(result.stderr.strip() or "Failed to save process list.", "error")
    utils.pause()


def reload_all():
    if not require_pm2():
        return
    os.system("clear")
    utils.print_menu_name("Reload all apps")
    result = subprocess.run(["pm2", "reload", "all"], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log("All apps reloaded.", "success")
    else:
        utils.log(result.stderr.strip() or "Reload failed.", "error")
    utils.pause()
