import os
import subprocess
from simple_term_menu import TerminalMenu
from modules import utils
from .interfaces import manage_interfaces
from .dns import manage_dns
from .gateway import manage_gateway
from .vlan import manage_vlan
from .service import manage_service, restart_service


def show_network_menu():
    last = 0

    while True:
        os.system("clear")
        utils.print_menu_name("Network Connectivity")

        options = [
            "Interfaces",                   # 0
            "DNS",                          # 1
            "Gateway",                      # 2
            "VLAN",                         # 3
            "",                             # 4
            "Ping test",                    # 5
            "Edit /etc/network/interfaces", # 6
            "",                             # 7
            "Service",                      # 8
            "",                             # 9
            "Back",                         # 10
        ]

        menu = utils.create_menu(options,last)
        choice = utils.show_menu(menu)

        if choice == 0:
            manage_interfaces()
        elif choice == 1:
            manage_dns()
        elif choice == 2:
            manage_gateway()
        elif choice == 3:
            manage_vlan()
        elif choice == 5:
            os.system("clear")
            utils.print_menu_name("Ping test")
            target = utils.ask_required("Target IP or hostname")
            if target is None:
                pass
            else:
                utils.log(f"Pinging {target}...", "info")
                try:
                    subprocess.run(["ping", "-c", "4", target])
                except KeyboardInterrupt:
                    pass
                utils.log("Ping finished.", "success")
                utils.pause()
        elif choice == 6:
            _edit_interfaces_file()
        elif choice == 8:
            manage_service()
        elif choice == 10 or choice is None:
            return
        last = choice


def _edit_interfaces_file():
    if not utils.is_binary_installed("nano"):
        utils.log("nano is not installed.", "error")
        if utils.choose(["yes", "no"], "Install nano?") != "yes":
            return
        subprocess.run(["sudo", "apt", "install", "nano", "-y"])
        if not utils.is_binary_installed("nano"):
            utils.log("Installation failed.", "error")
            utils.pause()
            return
    subprocess.run(["sudo", "nano", "/etc/network/interfaces"])
    if utils.choose(["yes", "no"], "Restart networking to apply changes?") == "yes":
        restart_service()

def run():
    show_network_menu()