from simple_term_menu import TerminalMenu
import subprocess
import os
from modules import utils
from .shared import remove_rule, show_chain, rule_exists, flush_chain, ensure_ip_forward


def masquerade():
    ensure_ip_forward()

    iface_out = utils.pick_interface("out")
    if iface_out is None:
        return
    src_ip = utils.ask_ip("Source IP/subnet for masquerading")
    if src_ip: cmd = ["sudo", "iptables", "-t", "nat", "-A", "POSTROUTING", "-s", src_ip, "-o", iface_out, "-j", "MASQUERADE"]
    else: cmd = ["sudo", "iptables", "-t", "nat", "-A", "POSTROUTING", "-o", iface_out, "-j", "MASQUERADE"]
    if rule_exists(cmd):
        utils.log("Rule already exists.", "info")
    else:
        utils.run_cmd(cmd)
        utils.log(f"Masquerade applied on interface {iface_out}.", "success")


def manage_postrouting():
    last = 0
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > POSTROUTING (NAT)")

        options = [
            "Add rule",
            "Remove rule",
            "",
            "Show",
            "",
            "Back",
            "Flush"
        ]

        menu = TerminalMenu(options,cursor_index=last, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            masquerade()
        elif choice == 1:
            remove_rule("POSTROUTING", "nat")
        elif choice == 3:
            show_chain("POSTROUTING", "nat")
        elif choice == 5 or choice is None:
            break
        elif choice == 6:
            flush_chain("POSTROUTING", "nat")

        last = choice

def prerouting():
    ensure_ip_forward()
    
    iface_in = utils.pick_interface("in")
    if iface_in is None: return

    while True:
        src_ip = utils.ask("Source IP/subnet (optional)")
        if src_ip is None: return
        if not src_ip or utils.check_ip(src_ip): break
        utils.log("Invalid IP.", "error")


    while True:
        port = utils.ask_required("Select port from which to forward")
        if port is None: return
        if utils.check_port(port): break
        utils.log("Invalid port.", "error")     

    while True:
        des_ip = utils.ask_required("Select destination IP address")
        if des_ip is None: return
        if utils.check_ip(des_ip): break
        utils.log("Invalid IP.", "error")  

    while True:
        des_port = utils.ask_required("Select port to which to forward")
        if des_port is None: return
        if utils.check_port(des_port): break
        utils.log("Invalid port.", "error") 

    protocol = utils.choose(["tcp", "udp"], "Select protocol")
    
    dnat_cmd = ["sudo", "iptables", "-t", "nat", "-A", "PREROUTING", "-i", iface_in]
    if src_ip: dnat_cmd += ["-s", src_ip]
    dnat_cmd +=  ["-p", protocol, "--dport", port, "-j", "DNAT", "--to-destination", f"{des_ip}:{des_port}"]

    
    if rule_exists(dnat_cmd):
        utils.log("Rule already exists.", "info")
    else:

        result = subprocess.run(dnat_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            utils.log("Failed to add DNAT rule", "error")
            utils.pause()
            return
        utils.log(f"{iface_in}:{port} -> {des_ip}:{des_port} (DNAT)", "success")

        check_cmd = ["sudo", "iptables", "-C", "FORWARD", "-i", iface_in, "-d", des_ip, "-p", protocol, "--dport", des_port]
        if src_ip: check_cmd += ["-s", src_ip]
        check_cmd += ["-j", "ACCEPT"]
        check = subprocess.run(check_cmd, capture_output=True)

        if check.returncode != 0:
            forward_cmd = ["sudo", "iptables", "-A", "FORWARD", "-i", iface_in, "-d", des_ip, "-p", protocol, "--dport", des_port]
            if src_ip: forward_cmd += ["-s", src_ip]
            forward_cmd += ["-j", "ACCEPT"]

            utils.run_cmd(forward_cmd)
            utils.log(f"FORWARD rule added automatically for {des_ip}:{des_port}.", "info")
        utils.pause()


    


def manage_prerouting():
    last = 0
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > PREROUTING (DNAT)")

        options = [
            "Add rule",
            "Remove rule",
            "",
            "Show",
            "Back",
            "Flush"
        ]

        menu = TerminalMenu(options,cursor_index=last, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            prerouting()
        elif choice == 1:
            remove_rule("PREROUTING", "nat")
        elif choice == 3:
            show_chain("PREROUTING", "nat")
        elif choice == 4 or choice is None:
            break
        elif choice == 5:
            flush_chain("PREROUTING", "nat")
        
        last = choice
