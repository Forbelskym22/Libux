import os
import subprocess
from modules import utils

def show_hostname(pause=True):
    os.system("clear")
    utils.print_menu_name("Hostname")

    result = subprocess.run(["hostnamectl", "status"], capture_output=True, text=True)
    print(f"{utils.WHITE}{result.stdout}{utils.RESET}")

    if pause:
        utils.pause()

def set_hostname():
    os.system("clear")
    utils.print_menu_name("Set hostname")
    show_hostname(pause=False)

    hostname = utils.ask_required("New hostname")
    if hostname is None:
        return
    
    try:
        result = subprocess.run(["sudo", "hostnamectl", "set-hostname", hostname], capture_output=True, text=True)
        if result.returncode == 0:
            utils.log(f"Hostname set to {hostname}.", "success")
        else:
            utils.log(result.stderr.strip(), "error")
    except KeyboardInterrupt:
        utils.log("Cancelled.", "info")
    utils.pause()

def manage_hostname():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Hostname")

        options = [
            "Show",             # 0
            "Set",              # 1
            "",                 # 2
            "Back"              # 3
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_hostname()
        elif choice == 1:
            set_hostname()
        elif choice == 3 or choice is None:
            return
        
        last = choice
