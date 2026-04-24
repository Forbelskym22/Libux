import os
from modules import utils
from .shared import is_pm2_installed
from .install import install_pm2, remove_pm2
from .apps import show_status, start_app, stop_app, restart_app, delete_app, view_logs
from .ecosystem import setup_startup, list_ecosystem, save_ecosystem, reload_all


def show_pm2_menu():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("PM2")

        status = f"{utils.GREEN}installed{utils.RESET}" if is_pm2_installed() else f"{utils.RED}not installed{utils.RESET}"
        print(f"  {utils.GRAY}PM2: {status}{utils.RESET}\n")

        options = [
            "Install PM2",    # 0
            "Remove PM2",     # 1
            "",               # 2
            "Status",         # 3
            "Start app",      # 4
            "Stop app",       # 5
            "Restart app",    # 6
            "Delete app",     # 7
            "View logs",      # 8
            "",               # 9
            "Setup startup",  # 10
            "List ecosystem", # 11
            "Save ecosystem", # 12
            "Reload all",     # 13
            "",               # 14
            "Back",           # 15
        ]

        choice = utils.show_menu(utils.create_menu(options, last))

        if choice == 0:
            install_pm2()
        elif choice == 1:
            remove_pm2()
        elif choice == 3:
            show_status()
        elif choice == 4:
            start_app()
        elif choice == 5:
            stop_app()
        elif choice == 6:
            restart_app()
        elif choice == 7:
            delete_app()
        elif choice == 8:
            view_logs()
        elif choice == 10:
            setup_startup()
        elif choice == 11:
            list_ecosystem()
        elif choice == 12:
            save_ecosystem()
        elif choice == 13:
            reload_all()
        elif choice == 15 or choice is None:
            return

        last = choice


def run():
    show_pm2_menu()
