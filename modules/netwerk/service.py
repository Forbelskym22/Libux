import os
import subprocess
from modules import utils

NET_SERVICE = "networking"


def show_status():
    os.system("clear")
    utils.print_menu_name("Networking service status")
    subprocess.run(["sudo", "systemctl", "status", NET_SERVICE, "--no-pager"])
    utils.pause()


def _action(verb, past):
    try:
        result = subprocess.run(
            ["sudo", "systemctl", verb, NET_SERVICE],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            utils.log(f"Networking service {past}.", "success")
        else:
            utils.log(result.stderr.strip() or f"Networking service failed to {verb}.", "error")
    except KeyboardInterrupt:
        utils.log("Cancelled.", "info")
    utils.pause()


def start_service():
    _action("start", "started")


def stop_service():
    _action("stop", "stopped")


def restart_service():
    _action("restart", "restarted")


def manage_service():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Networking Service")

        options = [
            "Status",   # 0
            "Start",    # 1
            "Stop",     # 2
            "Restart",  # 3
            "",         # 4
            "Back",     # 5
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
        elif choice == 5 or choice is None:
            return

        last = choice
