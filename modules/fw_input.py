from simple_term_menu import TerminalMenu
import subprocess
import shlex
import os
from modules import utils
from modules.fw_shared import remove_rule, show_chain


def input_allow_port(port, proto="tcp"):
    subprocess.run(["sudo", "iptables", "-A", "INPUT", "-p", proto, "--dport", str(port), "-j", "ACCEPT"])
    utils.log(f"Allowed {proto.upper()} port {port} on INPUT.", "success")


def input_allow_custom():
    try:
        proto =utils.choose(["tcp","udp"], "Choose protocol.")

        port = input(f"{utils.WHITE}Port: {utils.RESET}")
        while True:
            if utils.check_port(port):
                input_allow_port(port, proto)
                return
            else:
                utils.log("Invalid port.", "error")
                return
    except KeyboardInterrupt:
        pass


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
            subprocess.run(["sudo", "iptables", "-A", "INPUT", "-p", "icmp", "-j", "ACCEPT"])
            utils.log("ICMP (ping) allowed on INPUT.", "success")
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
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > INPUT Chain")

        options = [
            "Add rule",
            "Remove rule",
            "",
            "Show",
            "Back"
        ]

        menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
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
            show_chain("INPUT")
        elif choice == 4 or choice is None:
            break
