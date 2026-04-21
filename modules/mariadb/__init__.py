import os
from modules import utils
from .service import manage_service, is_installed, install_mariadb, set_root_password
from .phpmyadmin import install_phpmyadmin, is_installed as pma_is_installed


def show_mariadb_menu():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("MariaDB")

        pma_tag = " (installed)" if pma_is_installed() else ""
        options = [
            "Service",                      # 0
            "Set root password",            # 1
            f"Install phpMyAdmin{pma_tag}", # 2
            "",                             # 3
            "Back",                         # 4
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            manage_service()
        elif choice == 1:
            set_root_password()
        elif choice == 2:
            install_phpmyadmin()
        elif choice == 4 or choice is None:
            return

        last = choice


def run():
    if not is_installed():
        os.system("clear")
        utils.print_menu_name("MariaDB")
        utils.log("mariadb-server is not installed.", "error")
        confirm = utils.choose(["Install", "Back"])
        if confirm == "Install":
            install_mariadb()
        else:
            return

    if is_installed():
        show_mariadb_menu()
