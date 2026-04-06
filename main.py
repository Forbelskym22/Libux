import sys
import os
from simple_term_menu import TerminalMenu
from modules import firewall
from modules import utils

def main():
    if os.geteuid() != 0:
        utils.log("This script requires root permissions. Run with sudo.", "error")
        sys.exit(1)
    options = ["Firewall (iptables)", "Ukončit Libux"]
    
    while True:
        os.system('clear')
        terminal_menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, menu_cursor_style=utils.MENU_CURSOR_STYLE)

        menu_entry_index = utils.show_menu(terminal_menu)
        
        if menu_entry_index == 0:
            firewall.run()
        elif menu_entry_index == 1 or menu_entry_index is None:
            utils.log("Ukončuji Libux...", "info")
            sys.exit(0)

if __name__ == "__main__":
    main()