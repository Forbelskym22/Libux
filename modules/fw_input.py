from simple_term_menu import TerminalMenu
import subprocess
import shlex
import os
from modules import utils
from modules.fw_shared import remove_rule, show_chain, rule_exists, ask


def input_allow_port(port, proto="tcp"):
    while True:
        src_ip = ask("Choose source ip / subnet")
        if src_ip is None: return
        if not src_ip or utils.check_ip(src_ip): break
        utils.log("Invalid IP/subnet.", "error")

    if(src_ip):
        cmd = ["sudo", "iptables", "-A", "INPUT", "-s", src_ip, "-p", proto, "--dport", str(port), "-j", "ACCEPT"]
    else:
        cmd = ["sudo", "iptables", "-A", "INPUT", "-p", proto, "--dport", str(port), "-j", "ACCEPT"]
    if rule_exists(cmd):
        utils.log("Rule already exists.", "info")
    else:
        subprocess.run(cmd)
        utils.log(f"Allowed {proto.upper()} port {port} on INPUT.", "success")



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
            icmp_cmd = ["sudo", "iptables", "-A", "INPUT", "-p", "icmp", "-j", "ACCEPT"]
            if rule_exists(icmp_cmd):
                utils.log("Rule already exists.", "info")
            else:
                subprocess.run(icmp_cmd)
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
