import sys
from simple_term_menu import TerminalMenu
from modules import firewall
from modules import utils

def main():
    options = ["Firewall (iptables)", "Ukončit Libux"]
    terminal_menu = TerminalMenu(options, title="=== LIBUX Server Configurator ===")
    
    while True:
        menu_entry_index = terminal_menu.show()
        
        if menu_entry_index == 0:
            firewall.run()
        elif menu_entry_index == 1 or menu_entry_index is None:
            utils.log("Ukončuji Libux...", "info")
            sys.exit(0)

if __name__ == "__main__":
    main()