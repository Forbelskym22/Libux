from simple_term_menu import TerminalMenu
import subprocess
import os
from modules import utils
from .shared import remove_rule, show_chain, rule_exists, flush_chain, toggle_policy, allow_port, allow_icmp



def input_allow_port(port, proto="tcp"):
    src_ip = utils.ask_ip("Source IP/subnet to allow")
    if src_ip is None: return
    allow_port("INPUT", port, proto, src_ip=src_ip or None)



def input_allow_custom():
    proto = utils.choose(["tcp", "udp"], "Choose protocol.")
    if proto is None:
        return

    while True:
        try:
            port = input(f"{utils.WHITE}Port: {utils.RESET}")
        except KeyboardInterrupt:
            return
        if utils.check_port(port):
            input_allow_port(port, proto)
            return
        utils.log("Invalid port.", "error")



def input_add_rule():
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > INPUT Chain > Add rule")

        options = [
            "HTTP (80/tcp)",
            "HTTPS (443/tcp)",
            "HTTP + HTTPS",
            "ICMP (ping)",
            "Custom port",
            "",
            "Back"
        ]

        menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            input_allow_port(80)
        elif choice == 1:
            input_allow_port(443)
        elif choice == 2:
            input_allow_port(80)
            input_allow_port(443)
        elif choice == 3:
            src_ip = utils.ask_ip("Source IP/subnet to allow ICMP from")
            if src_ip is None: return
            allow_icmp("INPUT", src_ip=src_ip or None)

        elif choice == 4:
            input_allow_custom()
        elif choice == 6 or choice is None:
            break
        

        if choice in (0, 1, 2, 3, 4):
            try:
                input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
            except KeyboardInterrupt:
                pass


def manage_input_chain():
    last = 0
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > INPUT Chain")

        options = [
            "Add rule",
            "Remove rule",
            "",
            "Flush chain",
            "Toggle policy",
            "",
            "Show",
            "Back"
        ]

        menu = TerminalMenu(options,cursor_index=last, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            input_add_rule()
        elif choice == 1:
            remove_rule("INPUT")
            try:
                input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
            except KeyboardInterrupt:
                pass
        elif choice == 3:
            flush_chain("INPUT")
        elif choice == 4:
            toggle_policy("INPUT")
            try:
                input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
            except KeyboardInterrupt:
                pass
        elif choice == 6:
            show_chain("INPUT")
        elif choice == 7 or choice is None:
            break
        last = choice