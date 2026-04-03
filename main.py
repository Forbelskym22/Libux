import sys
from simple_term_menu import TerminalMenu
from modules import firewall

def main():
    options = ["Firewall (iptables)", "Ukončit Libux"]
    terminal_menu = TerminalMenu(options, title="=== LIBUX Server Configurator ===")
    
    while True:
        menu_entry_index = terminal_menu.show()
        
        if menu_entry_index == 0:
            firewall.run()
        elif menu_entry_index == 1 or menu_entry_index is None:
            print("Ukončuji Libux...")
            sys.exit(0)

if __name__ == "__main__":
    main()