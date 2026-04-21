import os
import subprocess
from simple_term_menu import TerminalMenu
from modules import utils
from .interfaces import manage_interfaces
from .dns import manage_dns
from .gateway import manage_gateway
from .hostname import manage_hostname
from .vlan import manage_vlan


def show_network_menu():
    last = 0

    while True:
        os.system("clear")
        utils.print_menu_name("Network Connectivity")

        options = [
            "Interfaces",               # 0
            "DNS",                      # 1
            "Gateway",                  # 2
            "Hostname",                 # 3
            "VLAN",                     # 4
            "",                         # 5
            "Ping test",                # 6
            "",                         # 7
            "Edit /etc/network/interfaces", # 8
            "Restart networking",       # 9
            "",                         # 10
            "Back",                     # 11
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
            manage_hostname()
        elif choice == 4:
            manage_vlan()
        elif choice == 6:
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
        elif choice == 8:
            _edit_interfaces_file()
        elif choice == 9:
            _restart_networking()
        elif choice == 11 or choice is None:
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
        _restart_networking()


def _restart_networking():
    os.system("clear")
    utils.print_menu_name("Restart networking")
    utils.log("Restarting networking.service...", "info")
    result = subprocess.run(["sudo", "systemctl", "restart", "networking"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to restart networking.", "error")
    else:
        utils.log("networking.service restarted.", "success")
    utils.pause()

def run():
    show_network_menu()