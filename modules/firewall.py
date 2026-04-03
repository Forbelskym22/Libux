from simple_term_menu import TerminalMenu
from modules import utils

def run():
    print("\n--- Spouštím konfiguraci Firewallu (iptables) ---")

    if utils.is_service_installed("iptables"):
        print("\n[OK] iptables nalezeny. Spouštím konfiguraci...")
        input("Stiskni Enter pro návrat do hlavního menu...")
    else:
        # List with options
        options = ["Install iptables","Back to main menu"]
        # Create object of the menu
        menu = TerminalMenu(options,title="[!] iptables aren't installed.")
        # Render the object
        choice = menu.show()

        # reaction to the choice
        if choice == 0:
            print("\nStarting an installation of iptables...")
            input("\nPress Enter to continue...")
        elif choice == 1 or choice is None:
            return
        
