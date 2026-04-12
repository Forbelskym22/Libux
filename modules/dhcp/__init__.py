import os
from modules import utils
from .subnets import manage_subnets, add_subnet
from .leases import manage_leases
from .service import manage_service, is_installed, install_dhcp, has_subnet


def show_dhcp_menu():
    last = 0

    while True:
        os.system("clear")
        utils.print_menu_name("DHCP Server")

        # upozorni pokud není subnet
        if not has_subnet():
            utils.log("No subnet configured — service won't start without one.", "info")
            print()

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
    if not is_installed():
        os.system("clear")
        utils.print_menu_name("DHCP Server")
        utils.log("isc-dhcp-server is not installed.", "error")
        confirm = utils.choose(["Install", "Back"])
        if confirm == "Install":
            install_dhcp()
        else:
            return

    if is_installed():
        show_dhcp_menu()
