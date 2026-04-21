import sys
import os
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
from modules import packages


# (label, callback). Empty label = separator. Callback None = exit.
MENU = [
    ("Firewall (iptables)", firewall.run),
    ("Netwerk",             netwerk.run),
    ("DHCP",                dhcp.run),
    ("SSH",                 ssh.run),
    ("Apache2",             apache2.run),
    ("MariaDB",             mariadb.run),
    ("Routing",             routing.run),
    ("Users & Groups",      users.run),
    ("Quotas",              perms.quotas_menu),
    ("Permissions",         perms.permissions_menu),
    ("",                    None),
    ("Packages",            packages.manage_packages),
    ("Settings",            settings.manage_settings),
    ("",                    None),
    ("Exit Libux",          None),  # sentinel: exit
]


def main():
    if os.geteuid() != 0:
        utils.log("This script requires root permissions. Run with sudo.", "error")
        sys.exit(1)

    options = [label for label, _ in MENU]
    exit_idx = len(MENU) - 1  # last entry is Exit
    last = 0

    while True:
        os.system('clear')
        utils.print_menu_name("Libux v1.0.1")
        terminal_menu = utils.create_menu(options, last)
        idx = utils.show_menu(terminal_menu)

        if idx is None or idx == exit_idx:
            utils.log("Exiting Libux...", "info")
            sys.exit(0)

        callback = MENU[idx][1]
        if callback is not None:
            callback()

        last = idx


if __name__ == "__main__":
    main()
