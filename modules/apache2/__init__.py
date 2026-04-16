import os
from modules import utils
from .service import manage_service, is_installed, install_apache
from .config import manage_config
from .vhosts import manage_vhosts, manage_pages
from .modules import manage_modules
from .logs import manage_logs

def show_apache_menu():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Apache2")

        options = [
            "Service",          # 0
            "Config",           # 1
            "Virtual Hosts",    # 2
            "Page",             # 3
            "Modules",          # 4
            "Logs",             # 5
            "",                 # 6
            "Back",             # 7
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            manage_service()
        elif choice == 1:
            manage_config()
        elif choice == 2:
            manage_vhosts()
        elif choice == 3:
            manage_pages()
        elif choice == 4:
            manage_modules()
        elif choice == 5:
            manage_logs()
        elif choice == 7 or choice is None:
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
