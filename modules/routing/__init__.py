import os
from modules import utils
from .routes import show_routes, add_route, remove_route, set_default_gateway

def show_routing_menu():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Routing")

        options = [
            "Show routing table",   # 0
            "Add static route",     # 1
            "Remove route",         # 2
            "Set default gateway",  # 3
            "",                     # 4
            "Back",                 # 5
        ]

        choice = utils.show_menu(utils.create_menu(options, last))

        if choice == 0:
            show_routes()
        elif choice == 1:
            add_route()
        elif choice == 2:
            remove_route()
        elif choice == 3:
            set_default_gateway()
        elif choice == 5 or choice is None:
            return

        last = choice

def run():
    show_routing_menu()
