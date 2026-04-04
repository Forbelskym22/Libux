from simple_term_menu import TerminalMenu
import subprocess
import shlex
import os
from modules import utils
from modules.fw_shared import ask, remove_rule


def masquerade():
    iface_out = ask("Select interface for Masquerade")
    if iface_out is None:
        return
    subprocess.run(shlex.split(f"sudo iptables -t nat -A POSTROUTING -o {iface_out} -j MASQUERADE"))
    utils.log(f"Masquerade applied on interface {iface_out}.", "success")


def manage_postrouting():
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > POSTROUTING (NAT)")

        options = [
            "Add rule",
            "Remove rule",
            "",
            "Back"
        ]

        menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            masquerade()
        elif choice == 1:
            remove_rule("POSTROUTING", "nat")
        elif choice == 3 or choice is None:
            break


def manage_prerouting():
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > PREROUTING (DNAT)")

        options = [
            "Add rule",
            "Remove rule",
            "",
            "Back"
        ]

        menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            pass  # TODO: DNAT / port forwarding
        elif choice == 1:
            remove_rule("PREROUTING", "nat")
        elif choice == 3 or choice is None:
            break
