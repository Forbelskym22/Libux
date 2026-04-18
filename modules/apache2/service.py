import os
import subprocess
from modules import utils
from .shared import APACHE_SERVICE, APACHE_CONF

def is_installed():
    result = subprocess.run(["dpkg", "-l", "apache2"], capture_output=True)
    return result.returncode == 0 and utils.is_binary_installed("apache2ctl")

def install_apache():
    os.system("clear")
    utils.print_menu_name("Install Apache2")
    utils.log("Installing apache2...", "info")

    result = subprocess.run(["sudo", "apt", "update"], capture_output=True, text=True)
    if result.returncode != 0:
        utils.log("apt update failed", "error")
        utils.pause()
        return

    result = subprocess.run(["sudo", "apt", "install", "apache2", "-y"])

    if is_installed():
        utils.log("apache2 installed.", "success")
    else:
        utils.log("Installation failed.", "error")

    utils.pause()

def show_status():
    os.system("clear")
    utils.print_menu_name("Apache2 Service status")
    subprocess.run(["sudo", "systemctl", "status", APACHE_SERVICE, "--no-pager"])
    utils.pause()

def start_service():
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "start", APACHE_SERVICE],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            utils.log("Apache2 service started.", "success")
        else:
            utils.log("Apache2 service failed to start.", "error")
    except KeyboardInterrupt:
        utils.log("Cancelled.", "info")
    utils.pause()

def stop_service():
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "stop", APACHE_SERVICE],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            utils.log("Apache2 service stopped.", "success")
        else:
            utils.log("Apache2 service failed to stop.", "error")
    except KeyboardInterrupt:
        utils.log("Cancelled.", "info")
    utils.pause()

def restart_service():
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "restart", APACHE_SERVICE],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            utils.log("Apache2 service restarted.", "success")
        else:
            utils.log("Apache2 service failed to restart.", "error")
    except KeyboardInterrupt:
        utils.log("Cancelled.", "info")
    utils.pause()

def reload_service():
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "reload", APACHE_SERVICE],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            utils.log("Apache2 service reloaded.", "success")
        else:
            utils.log("Apache2 service failed to reload.", "error")
    except KeyboardInterrupt:
        utils.log("Cancelled.", "info")
    utils.pause()

def config_test():
    os.system("clear")
    utils.print_menu_name("Test Config")
    result = subprocess.run(["sudo", "apache2ctl", "configtest"], capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        utils.log("Syntax OK.", "success")
    else:
        utils.log("Config error:", "error")
        print(f"\n{utils.GRAY}{output}{utils.RESET}\n")
    utils.pause()

def manage_service():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Apache2 Service")

        options = [
            "Status",       # 0
            "Start",        # 1
            "Stop",         # 2
            "Restart",      # 3
            "Reload",       # 4
            "Test config",  # 5
            "",             # 6
            "Back",         # 7
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_status()
        elif choice == 1:
            start_service()
        elif choice == 2:
            stop_service()
        elif choice == 3:
            restart_service()
        elif choice == 4:
            reload_service()
        elif choice == 5:
            config_test()
        elif choice == 7 or choice is None:
            return

        last = choice
