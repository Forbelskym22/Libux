import os
from modules import utils
from .users import show_users, add_user, remove_user, change_password, toggle_lock, toggle_sudo
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
            "Sudo access",       # 5
            "",                  # 6
            "Show groups",       # 7
            "Add group",         # 8
            "Remove group",      # 9
            "Group membership",  # 10
            "",                  # 11
            "Back",              # 12
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
        elif choice == 5:
            toggle_sudo()
        elif choice == 7:
            show_groups()
        elif choice == 8:
            add_group()
        elif choice == 9:
            remove_group()
        elif choice == 10:
            manage_membership()
        elif choice == 12 or choice is None:
            return

        last = choice

def run():
    show_users_menu()
