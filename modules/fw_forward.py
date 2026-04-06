from simple_term_menu import TerminalMenu
import subprocess
import os
from modules import utils
from modules.fw_shared import ask, remove_rule, show_chain


def forward_allow_traffic():
    os.system('clear')
    utils.print_menu_name("Firewall > FORWARD Chain > Allow traffic")

    iface_in  = ask("From interface (e.g. eth0)")
    if iface_in is None: return
    iface_out = ask("To interface (e.g. eth1)")
    if iface_out is None: return
    src       = ask("Source IP/subnet (e.g. 192.168.1.0/24)")
    if src is None: return
    dst       = ask("Destination IP/subnet (e.g. 10.0.0.5)")
    if dst is None: return

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
        if port and port.isdigit():
            cmd += ["--dport", port]
    cmd += ["-j", "ACCEPT"]

    subprocess.run(cmd)
    utils.log("Forward rule added.", "success")


def forward_allow_es_rel():
    try:
        permission = input(f"{utils.WHITE}Allow related/established{utils.GRAY} (y/n): {utils.RESET}").strip()
    except KeyboardInterrupt:
        return
    if permission != "y":
        return

    iface_in  = ask("From interface (e.g. eth1 = LAN)")
    if iface_in is None: return
    iface_out = ask("To interface (e.g. eth0 = WAN)")
    if iface_out is None: return

    cmd = ["sudo", "iptables", "-A", "FORWARD"]
    if iface_in:  cmd += ["-i", iface_in]
    if iface_out: cmd += ["-o", iface_out]
    cmd += ["-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"]

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
            subprocess.run(["sudo", "iptables", "-A", "FORWARD", "-p", "icmp", "-j", "ACCEPT"])
            utils.log("ICMP (ping) allowed on FORWARD.", "success")
        elif choice == 4 or choice is None:
            break

        if choice in (0, 1, 2):
            try:
                input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
            except KeyboardInterrupt:
                pass


def manage_forward_chain():
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > FORWARD Chain")

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
            forward_add_rule()
        elif choice == 1:
            remove_rule("FORWARD")
            try:
                input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
            except KeyboardInterrupt:
                pass
        elif choice == 3:
            show_chain("FORWARD")
        elif choice == 4 or choice is None:
            break
