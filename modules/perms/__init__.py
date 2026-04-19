import os
from modules import utils
from .quotas import quotas_menu
from .permissions import permissions_menu

__all__ = ["quotas_menu", "permissions_menu", "run"]

def show_perms_menu():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Disk Quotas & Permissions")

        options = [
            "Quotas",       # 0
            "Permissions",  # 1
            "",             # 2
            "Back",         # 3
        ]

        choice = utils.show_menu(utils.create_menu(options, last))

        if choice == 0:
            quotas_menu()
        elif choice == 1:
            permissions_menu()
        elif choice == 3 or choice is None:
            return

        last = choice

def run():
    show_perms_menu()
