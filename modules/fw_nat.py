from simple_term_menu import TerminalMenu
import subprocess
import shlex
import os
from modules import utils
from modules.fw_shared import ask, ask_required, remove_rule, show_chain


def masquerade():
    iface_out = utils.pick_interface("out")
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
            "Show",
            "Back"
        ]

        menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            masquerade()
        elif choice == 1:
            remove_rule("POSTROUTING", "nat")
        elif choice == 3:
            show_chain("POSTROUTING", "nat")
        elif choice == 4 or choice is None:
            break

def prerouting():
    iface_in = utils.pick_interface("in")
    if iface_in is None: return

    while True:
        port = ask_required("Select port from which to forward")
        if port is None: return
        if utils.check_port(port): break
        utils.log("Invalid port.", "error")     


    while True:
        des_ip = ask_required("Select destination IP address")
        if des_ip is None: return
        if utils.check_ip(des_ip): break
        utils.log("Invalid IP.", "error")  

    while True:
        des_port = ask_required("Select port to which to forward")
        if des_port is None: return
        if utils.check_port(des_port): break
        utils.log("Invalid port.", "error") 
    
    subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "PREROUTING", "-i", iface_in, "-p", "tcp", "--dport", port, "-j", "DNAT", "--to-destination", f"{des_ip}:{des_port}"])
    utils.log(f"{iface_in}:{port} → {des_ip}:{des_port} (DNAT)", "success")

    check = subprocess.run(["sudo", "iptables", "-C", "FORWARD", "-i", iface_in, "-d", des_ip, "-p", "tcp", "--dport", des_port, "-j", "ACCEPT"])
    if check.returncode == 1:
        subprocess.run(["sudo", "iptables", "-A", "FORWARD", "-i", iface_in, "-d", des_ip, "-p", "tcp", "--dport", des_port, "-j", "ACCEPT"])
        utils.log(f"FORWARD rule added automatically for {des_ip}:{des_port}.", "info")

    


def manage_prerouting():
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > PREROUTING (DNAT)")

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
            prerouting()
        elif choice == 1:
            remove_rule("PREROUTING", "nat")
        elif choice == 3:
            show_chain("PREROUTING", "nat")
        elif choice == 4 or choice is None:
            break
