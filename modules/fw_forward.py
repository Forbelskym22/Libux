from simple_term_menu import TerminalMenu
import subprocess
import os
from modules import utils
from modules.fw_shared import remove_rule, show_chain, rule_exists, flush_chain, toggle_policy, allow_icmp


def forward_allow_traffic():
    os.system('clear')
    utils.print_menu_name("Firewall > FORWARD Chain > Allow traffic")

    iface_in  = utils.pick_interface("in")
    if iface_in is None: return
    iface_out = utils.pick_interface("out")
    if iface_out is None: return
    
    src = ask("Source IP/subnet (e.g. 192.168.1.0/24)")

    if src is None: return

    if src and not utils.check_ip(src):
        utils.log("Invalid IP.", "error")
        return
    
    dst = ask("Destination IP/subnet (e.g. 10.0.0.5)")

    if dst is None: return

    if dst and not utils.check_ip(dst):
        utils.log("Invalid IP.", "error")
        return

    proto_menu = TerminalMenu(["tcp", "udp", "any"], cycle_cursor=True, clear_screen=False, menu_cursor_style=utils.MENU_CURSOR_STYLE)
    proto_choice = utils.show_menu(proto_menu)
    if proto_choice is None: return
    proto = ["tcp", "udp", "any"][proto_choice]

    port = ""
    if proto in ("tcp", "udp"):
        port = ask("Destination port")
        if port is None: return

    cmd = ["sudo", "iptables", "-A", "FORWARD"]
    if iface_in:  cmd += ["-i", iface_in]
    if iface_out: cmd += ["-o", iface_out]
    if src:       cmd += ["-s", src]
    if dst:       cmd += ["-d", dst]
    if proto in ("tcp", "udp"):
        cmd += ["-p", proto]
        if utils.check_port(port):
            cmd += ["--dport", port]
    cmd += ["-j", "ACCEPT"]


    if rule_exists(cmd):
        utils.log("Rule already exists.", "info")
    else:
        subprocess.run(cmd)
        utils.log("Forward rule added.", "success")
    


def forward_allow_es_rel():
    
    permission = utils.choose(["yes", "no"], "Allow related/established")
    
    if permission != "yes":
        return

    src_ip = utils.ask_ip("Source IP/subnet to allow established/related from")
    if src_ip is None: return

    iface_in  = utils.pick_interface("in")
    if iface_in is None: return

    iface_out = utils.pick_interface("out")
    if iface_out is None: return

    cmd = ["sudo", "iptables", "-A", "FORWARD"]
    if src_ip: cmd += ["-s", src_ip]
    if iface_in:  cmd += ["-i", iface_in]
    if iface_out: cmd += ["-o", iface_out]
    cmd += ["-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"]

    if rule_exists(cmd):
        utils.log("Rule already exists.", "info")
    else:
        subprocess.run(cmd)
        utils.log("Established/related traffic allowed on FORWARD.", "success")



def forward_add_rule():
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > FORWARD Chain > Add rule")

        options = [
            "Allow traffic",
            "Allow established/related",
            "Allow ICMP (ping)",
            "",
            "Back"
        ]

        menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            forward_allow_traffic()
        elif choice == 1:
            forward_allow_es_rel()
        elif choice == 2:
            allow_icmp("FORWARD")
                    
        elif choice == 4 or choice is None:
            break
        

        if choice in (0, 1, 2):
            try:
                input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
            except KeyboardInterrupt:
                pass


def manage_forward_chain():
    last = 0
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > FORWARD Chain")

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
            forward_add_rule()
        elif choice == 1:
            remove_rule("FORWARD")
            try:
                input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
            except KeyboardInterrupt:
                pass
        elif choice == 3:
            flush_chain("FORWARD")
        elif choice == 4:
            toggle_policy("FORWARD")
            try:
                input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
            except KeyboardInterrupt:
                pass
        elif choice == 6:
            show_chain("FORWARD")
        elif choice == 7 or choice is None:
            break

        last = choice