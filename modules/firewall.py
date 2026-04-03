from simple_term_menu import TerminalMenu
import subprocess
from modules import utils

def run():
    utils.log("Spouštím konfiguraci Firewallu (iptables)", "info")
    if utils.is_service_installed("iptables"):
        utils.log(" iptables nalezeny. Spouštím konfiguraci...", "info")
        utils.log("Stiskni Enter pro návrat do hlavního menu...", "info")

    else:
        # List with options
        options = ["Install iptables","Back to main menu"]
        # Create object of the menu

        utils.print_menu_name("Firewall isn't installed.")
        menu = TerminalMenu(options)
        # Render the object
        choice = menu.show()

        # reaction to the choice
        if choice == 0:
            utils.log("Starting an installation of iptables...", "info")


            # run commands in terminal
            subprocess.run(["sudo", "apt", "update"])
            subprocess.run(["sudo","apt","install","iptables","-y"])

            

            if utils.is_service_installed("iptables"):
                utils.log("iptables installed.", "success")
            else:
                
                utils.log("Installation failed! Check logs or network connection.", "error")
            utils.log("Press Enter to continue...", "info")
        elif choice == 1 or choice is None:
            return
        
