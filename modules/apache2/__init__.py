import os
from modules import utils
from .service import manage_service, is_installed, install_apache
from .sites import manage_sites
from .modules import manage_modules

def show_apache_menu():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Apache2")

        options = [
            "Service",  # 0
            "Sites",    # 1
            "Modules",  # 2
            "",         # 3
            "Back",     # 4
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            manage_service()
        elif choice == 1:
            manage_sites()
        elif choice == 2:
            manage_modules()
        elif choice == 4 or choice is None:
            return

        last = choice

def run():
    if not is_installed():
        os.system("clear")
        utils.print_menu_name("Apache2")
        utils.log("apache2 is not installed.", "error")
        confirm = utils.choose(["Install", "Back"])
        if confirm == "Install":
            install_apache()
        else:
            return

    if is_installed():
        show_apache_menu()
