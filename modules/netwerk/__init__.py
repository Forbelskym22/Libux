import os
import subprocess
from simple_term_menu import TerminalMenu
from modules import utils


def show_network_menu():
    last = 0

    while True:
        os.system("clear")
        utils.print_menu_name("Network Connectivity")

        options = [
            "Interfaces",       # 0
            "DNS",              # 1
            "Gateway",          # 2   
            "Hostname",         # 3      
            "VLAN",             # 4   
            "",                 # 5
            "Ping test",        # 6       
            "",                 # 7
            "Back",             # 8  
        ]#

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

        elif choice == 8 or choice is None:
            return
        last = choice

def run():
    show_network_menu()