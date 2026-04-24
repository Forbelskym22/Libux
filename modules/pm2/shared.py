import subprocess
import json
from modules import utils

def is_pm2_installed():
    return utils.is_binary_installed("pm2")

def is_node_installed():
    return utils.is_binary_installed("nodejs")

def get_apps():
    try:
        result = subprocess.run(["pm2", "jlist"],capture_output=True, text=True)
        if result.returncode != 0:
            return []
        return [app["name"] for app in json.loads(result.stdout)]
    except Exception:
        return []
    
def pick_app(title):
    import os
    os.system("clear")
    utils.print_menu_name(title)
    apps = get_apps()
    if not apps:
        utils.log("No apps found in PM2", "info")
        utils.pause()
        return