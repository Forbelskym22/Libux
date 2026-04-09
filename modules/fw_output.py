from simple_term_menu import TerminalMenu
import subprocess
import shlex
import os
from modules import utils
from modules.fw_shared import remove_rule, show_chain, rule_exists, ask, flush_chain, toggle_policy


def output_allow_port(port, proto="tcp"):
    while True:
        des_ip = ask("Choose destination ip / subnet")
        if des_ip is None: return
        if not des_ip or utils.check_ip(des_ip): break
        utils.log("Invalid IP/subnet.", "error")

    if(des_ip):
        cmd = ["sudo", "iptables", "-A", "OUTPUT", "-d", des_ip, "-p", proto, "--dport", str(port), "-j", "ACCEPT"]
    else:
        cmd = ["sudo", "iptables", "-A", "OUTPUT", "-p", proto, "--dport", str(port), "-j", "ACCEPT"]
    if rule_exists(cmd):
        utils.log("Rule already exists.", "info")
    else:
        subprocess.run(cmd)
        utils.log(f"Allowed {proto.upper()} port {port} on OUTPUT.", "success")



def output_allow_custom():
    proto = utils.choose(["tcp", "udp"], "Choose protocol.")
    if proto is None:
        return

    while True:
        try:
            port = input(f"{utils.WHITE}Port: {utils.RESET}")
        except KeyboardInterrupt:
            return
        if utils.check_port(port):
            output_allow_port(port, proto)
            return
        utils.log("Invalid port.", "error")



def output_add_rule():
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > OUTPUT Chain > Add rule")

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
            output_allow_port(80)
        elif choice == 1:
            output_allow_port(443)
        elif choice == 2:
            output_allow_port(80)
            output_allow_port(443)
        elif choice == 3:
            while True:
                des_ip = ask("Choose destination ip / subnet")
                if des_ip is None: return
                if not des_ip or utils.check_ip(des_ip): break
                utils.log("Invalid IP/subnet.", "error")
            if des_ip:
                icmp_cmd = ["sudo", "iptables", "-A", "OUTPUT", "-d", des_ip, "-p", "icmp", "-j", "ACCEPT"]
            else:
                icmp_cmd = ["sudo", "iptables", "-A", "OUTPUT", "-p", "icmp", "-j", "ACCEPT"]

            if rule_exists(icmp_cmd):
                utils.log("Rule already exists.", "info")
            else:
                subprocess.run(icmp_cmd)
                utils.log("ICMP (ping) allowed on OUTPUT.", "success")

        elif choice == 4:
            output_allow_custom()
        elif choice == 6 or choice is None:
            break
        

        if choice in (0, 1, 2, 3, 4):
            try:
                input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
            except KeyboardInterrupt:
                pass


def manage_output_chain():
    last = 0
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > OUTPUT Chain")

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
            output_add_rule()
        elif choice == 1:
            remove_rule("OUTPUT")
            try:
                input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
            except KeyboardInterrupt:
                pass
        elif choice == 3:
            flush_chain("OUTPUT")
        elif choice == 4:
            toggle_policy("OUTPUT")
            try:
                input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
            except KeyboardInterrupt:
                pass
        elif choice == 6:
            show_chain("OUTPUT")
        elif choice == 7 or choice is None:
            break

        last = choice