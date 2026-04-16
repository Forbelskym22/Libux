import os
from modules import utils
from .service import manage_service, is_installed, install_apache
from .config import manage_config
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
            "Config",   # 2
            "Modules",  # 3
            "",         # 4
            "Back",     # 5
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            manage_service()
        elif choice == 1:
            manage_sites()
        elif choice == 2:
            manage_config()
        elif choice == 3:
            manage_modules()
        elif choice == 5 or choice is None:
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
