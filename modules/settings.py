import os
from modules import utils
import simple_term_menu

def manage_settings():
    while True:
        os.system("clear")
        utils.print_menu_name("Settings")

        verbose_status = "ON" if utils.VERBOSE else "OFF"
        options= [
            f"Verbose mode [{verbose_status}]",
            "",
            "Back"
        ]

        menu = simple_term_menu.TerminalMenu(options, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            utils.VERBOSE = not utils.VERBOSE
            utils.log(f"Verbose mode {'enabled' if utils.VERBOSE else 'disabled'}.", "success")
            utils.pause()
        elif choice == 3 or choice is None:
            break