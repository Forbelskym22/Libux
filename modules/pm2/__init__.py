import os
from modules import utils


def show_pm2_menu():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Disk Quotas & Permissions")

        options = [
        "Status",        # 0
        "Start app",     # 1
        "Stop app",      # 2
        "View logs",     # 3
        "Setup startup", # 4
        "",              # 5
        "Back"           # 6
    ]

        choice = utils.show_menu(utils.create_menu(options, last))

        if choice == 0:
            pass
        elif choice == 1:
            pass
        elif choice == 2:
            pass
        elif choice == 3:
            pass
        elif choice == 4:
            pass
        elif choice == 6 or choice is None:
            return

        last = choice

def run():        
    show_pm2_menu()
