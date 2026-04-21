import sys
import os
from simple_term_menu import TerminalMenu
from modules import firewall
from modules import utils
from modules import settings
from modules import netwerk
from modules import dhcp
from modules import ssh
from modules import apache2
from modules import mariadb
from modules import routing
from modules import users
from modules import perms

def main():
    if os.geteuid() != 0:
        utils.log("This script requires root permissions. Run with sudo.", "error")
        sys.exit(1)
    options = [
        "Firewall (iptables)", # 0
        "Netwerk",             # 1
        "DHCP",                # 2
        "SSH",                 # 3
        "Apache2",             # 4
        "MariaDB",             # 5
        "Routing",             # 6
        "Users & Groups",      # 7
        "Quotas",              # 8
        "Permissions",         # 9
        "",                    # 10
        "Settings",            # 11
        "",                    # 12
        "Exit Libux"           # 13
        ]
    last = 0
    while True:
        os.system('clear')
        utils.print_menu_name("Libux v0.9.0")
        terminal_menu = utils.create_menu(options,last)

        menu_entry_index = utils.show_menu(terminal_menu)

        if menu_entry_index == 0:
            firewall.run()
        elif menu_entry_index == 1:
            netwerk.run()
        elif menu_entry_index == 2:
            dhcp.run()
        elif menu_entry_index == 3:
            ssh.run()
        elif menu_entry_index == 4:
            apache2.run()
        elif menu_entry_index == 5:
            mariadb.run()
        elif menu_entry_index == 6:
            routing.run()
        elif menu_entry_index == 7:
            users.run()
        elif menu_entry_index == 8:
            perms.quotas_menu()
        elif menu_entry_index == 9:
            perms.permissions_menu()
        elif menu_entry_index == 11:
            settings.manage_settings()
        elif menu_entry_index == 13 or menu_entry_index is None:
            utils.log("Exiting Libux...", "info")
            sys.exit(0)
 
        last = menu_entry_index
        
if __name__ == "__main__":
    main()