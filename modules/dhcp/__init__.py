import os
import subprocess
from modules import utils
from .subnets import manage_subnets
from .leases import manage_leases
from .service import manage_service


def show_dhcp_menu():
    last = 0

    while True:
        os.system("clear")
        utils.print_menu_name("DHCP Server")

        options = [
            "Subnets",      # 0
            "Leases",       # 1
            "",             # 2
            "Service",      # 3
            "",             # 4
            "Back",         # 5
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            manage_subnets()
        elif choice == 1:
            manage_leases()
        elif choice == 3:
            manage_service()
        elif choice == 5 or choice is None:
            break

        last = choice


def run():
    show_dhcp_menu()
