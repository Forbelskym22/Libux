import os
from modules import utils
from .users import show_users, add_user, remove_user, change_password, toggle_lock
from .groups import show_groups, add_group, remove_group, manage_membership

def show_users_menu():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Users & Groups")

        options = [
            "Show users",        # 0
            "Add user",          # 1
            "Remove user",       # 2
            "Change password",   # 3
            "Lock / unlock",     # 4
            "",                  # 5
            "Show groups",       # 6
            "Add group",         # 7
            "Remove group",      # 8
            "Group membership",  # 9
            "",                  # 10
            "Back",              # 11
        ]

        choice = utils.show_menu(utils.create_menu(options, last))

        if choice == 0:
            show_users()
        elif choice == 1:
            add_user()
        elif choice == 2:
            remove_user()
        elif choice == 3:
            change_password()
        elif choice == 4:
            toggle_lock()
        elif choice == 6:
            show_groups()
        elif choice == 7:
            add_group()
        elif choice == 8:
            remove_group()
        elif choice == 9:
            manage_membership()
        elif choice == 11 or choice is None:
            return

        last = choice

def run():
    show_users_menu()
