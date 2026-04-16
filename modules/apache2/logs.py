import os
import subprocess
from modules import utils
from .vhosts import list_sites
from .shared import SITES_AVAILABLE

LOG_DIR = "/var/log/apache2"

def _get_site_name(site_conf):
    return site_conf.replace(".conf", "")

def _show_log(log_path, title):
    os.system("clear")
    utils.print_menu_name(title)
    result = subprocess.run(["sudo", "cat", log_path], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        utils.log("Log is empty or not found.", "info")
    else:
        print(result.stdout)
    utils.pause()

def show_access_log():
    os.system("clear")
    utils.print_menu_name("Access Log")

    available = list_sites(SITES_AVAILABLE)
    options = ["apache2 (global)"] + [_get_site_name(s) for s in available]

    choice = utils.choose(options, "Select site")
    if choice is None:
        return

    if choice == "apache2 (global)":
        log_path = f"{LOG_DIR}/access.log"
    else:
        log_path = f"{LOG_DIR}/{choice}_access.log"

    _show_log(log_path, f"Access Log - {choice}")

def show_error_log():
    os.system("clear")
    utils.print_menu_name("Error Log")

    available = list_sites(SITES_AVAILABLE)
    options = ["apache2 (global)"] + [_get_site_name(s) for s in available]

    choice = utils.choose(options, "Select site")
    if choice is None:
        return

    if choice == "apache2 (global)":
        log_path = f"{LOG_DIR}/error.log"
    else:
        log_path = f"{LOG_DIR}/{choice}_error.log"

    _show_log(log_path, f"Error Log - {choice}")

def manage_logs():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Logs")

        options = [
            "Access log",   # 0
            "Error log",    # 1
            "",             # 2
            "Back",         # 3
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_access_log()
        elif choice == 1:
            show_error_log()
        elif choice == 3 or choice is None:
            return

        last = choice
