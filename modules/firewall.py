from simple_term_menu import TerminalMenu
import subprocess
from modules import utils
import shlex
import os

def show_firewall():
    os.system('clear')
    utils.print_menu_name("Firewall rules")

    word_colors = {
        "INPUT": utils.PINK,
        "FORWARD": utils.PINK,
        "OUTPUT": utils.PINK,
        "ACCEPT": utils.GREEN,
        "DROP": utils.RED,
        "REJECT": utils.RED,
        "policy": utils.PURPLE,
        "all": utils.GRAY,
        "tcp": utils.WHITE,
        "udp": utils.WHITE,
        "icmp": utils.WHITE,
        "lo": utils.YELLOW
    }

    result = subprocess.run(shlex.split("sudo iptables -L -v"), capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if line.startswith("Chain"):
            colored = " ".join(
                f"{utils.GREEN}{w}{utils.RESET}" if w == "ACCEPT" else
                f"{utils.RED}{w}{utils.RESET}" if w in ("DROP", "REJECT") else
                f"{utils.PINK}{w}{utils.RESET}"
                for w in line.split(" ")
            )
            print(colored)
        else:
            colored = " ".join(
                f"{word_colors[w]}{w}{utils.RESET}" if w in word_colors else w
                for w in line.split(" ")
            )
            print(colored)

    try:
        input("\nPress Enter to return to menu...")
    except KeyboardInterrupt:
        pass

def ask(prompt):
    try:
        return input(f"{utils.WHITE}{prompt}{utils.GRAY} (Enter to skip): {utils.RESET}").strip()
    except KeyboardInterrupt:
        return None
        
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

        if choice in (0, 1, 2, 3):
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
            "Back"
        ]

        menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            forward_add_rule()
        elif choice == 1:
            forward_remove_rule()
            try:
                input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
            except KeyboardInterrupt:
                pass
        elif choice == 3 or choice is None:
            break

def input_allow_port(port, proto="tcp"):
    subprocess.run(["sudo", "iptables", "-A", "INPUT", "-p", proto, "--dport", str(port), "-j", "ACCEPT"])
    utils.log(f"Allowed {proto.upper()} port {port} on INPUT.", "success")

def input_allow_custom():
    try:
        proto = input(f"{utils.WHITE}Protocol (tcp/udp): {utils.RESET}").lower()
        if proto not in ("tcp", "udp"):
            utils.log("Invalid protocol.", "error")
            return
        port = input(f"{utils.WHITE}Port: {utils.RESET}")
        if not port.isdigit():
            utils.log("Invalid port.", "error")
            return
        input_allow_port(port, proto)
    except KeyboardInterrupt:
        pass

def input_remove_rule():
    result = subprocess.run(
        ["sudo", "iptables", "-L", "INPUT", "--line-numbers", "-n"],
        capture_output=True, text=True
    )
    lines = result.stdout.splitlines()
    rules = [(l.split()[0], l) for l in lines[2:] if l.strip()]

    if not rules:
        utils.log("No rules to remove.", "info")
        return

    options = [f"{num}  {rule}" for num, rule in rules]
    os.system('clear')
    utils.print_menu_name("Firewall > INPUT Chain > Remove rule")
    menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, menu_cursor_style=utils.MENU_CURSOR_STYLE)
    choice = utils.show_menu(menu)

    if choice is None:
        return

    line_num = rules[choice][0]
    subprocess.run(["sudo", "iptables", "-D", "INPUT", line_num])
    utils.log(f"Rule {line_num} removed.", "success")

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
            "Back"
        ]

        menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            input_add_rule()
        elif choice == 1:
            input_remove_rule()
            try:
                input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
            except KeyboardInterrupt:
                pass
        elif choice == 3 or choice is None:
            break

def setup_secure_baseline():
    os.system('clear')
    utils.print_menu_name("Secure Baseline Wizard")
    utils.log("This will reset INPUT chain and set a secure 'DROP' policy.", "info")

    def get_ssh_port():
        while True:
            try:
                choice = input(f"\n{utils.WHITE}Is your SSH running on port 22? (y/n): {utils.RESET}").lower()
            except KeyboardInterrupt:
                return None
            if choice == "y":
                return "22"
            elif choice == "n":
                try:
                    port = input(f"{utils.WHITE}Insert your SSH port: {utils.RESET}")
                except KeyboardInterrupt:
                    return None
                if port.isdigit():
                    return port
                utils.log("That's not a number!", "error")
            else:
                utils.log("Invalid input, type 'y' or 'n'.", "error")

    ssh_port = get_ssh_port()
    if ssh_port is None:
        utils.log("Wizard cancelled.", "info")
        return

    try:
        confirm = input(f"\n{utils.RED}WARNING: This will flush existing INPUT rules! Proceed? (y/n): {utils.RESET}").lower()
    except KeyboardInterrupt:
        utils.log("Wizard cancelled.", "info")
        return

    if confirm == 'y':
        utils.log("Applying core rules...", "info")

        core_commands = [
            "sudo iptables -F INPUT",
            "sudo iptables -A INPUT -i lo -j ACCEPT",
            "sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
            "sudo iptables -A INPUT -p udp --sport 53 -j ACCEPT",
            f"sudo iptables -A INPUT -p tcp --dport {ssh_port} -j ACCEPT"
        ]

        for cmd in core_commands:
            subprocess.run(shlex.split(cmd))

        try:
            if input(f"\n{utils.WHITE}Allow ICMP (Ping)? (y/n): {utils.RESET}").lower() == "y":
                subprocess.run(shlex.split("sudo iptables -A INPUT -p icmp -j ACCEPT"))
                utils.log("Ping allowed.", "success")
        except KeyboardInterrupt:
            pass

        subprocess.run(shlex.split("sudo iptables -P INPUT DROP"))
        subprocess.run(shlex.split("sudo iptables -P FORWARD DROP"))

        utils.log("Baseline applied! Policy set to DROP.", "success")
        try:
            input("\nPress Enter to return to menu...")
        except KeyboardInterrupt:
            pass
    else:
        utils.log("Wizard cancelled.", "info")
        try:
            input("\nPress Enter to return...")
        except KeyboardInterrupt:
            pass

def show_firewall_menu():
    while True:
        os.system('clear') 
        utils.print_menu_name("Firewall Configuration (iptables)")
        
        options = [
            "Default config (Wizard)",
            "INPUT Chain",
            "FORWARD Chain",
            "NAT / MANGLE",
            "",
            "Show",
            "Save",
            "Back"
        ]

        menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            setup_secure_baseline()
        elif choice == 1:
            manage_input_chain()
        elif choice == 2:
            manage_forward_chain()
        elif choice == 3:
            manage_forward_chain()
        elif choice == 5:
            show_firewall()
        elif choice == 6: 
            utils.log("Save function here...", "info")
            input("\nPress Enter to continue...")
        elif choice == 7 or choice is None:
            break

def show_firewall_installation_menu():
    if not utils.is_service_installed("iptables"):
        # List with options
        options = ["Install iptables","Back to main menu"]

        # Create object of the menu
        utils.print_menu_name("Firewall isn't installed.")
        menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, menu_cursor_style=utils.MENU_CURSOR_STYLE)

        # Render the object
        choice = utils.show_menu(menu)

        # reaction to the choice
        if choice == 0:
            utils.log("Starting an installation of iptables...", "info")

            # run commands in terminal
            subprocess.run(["sudo", "apt", "update"])
            subprocess.run(["sudo","apt","install","iptables","-y"])

            if utils.is_service_installed("iptables"):
                utils.log("iptables installed.", "success")
            else:
                
                utils.log("Installation failed! Check logs or network connection.", "error")
            utils.log("Press Enter to continue...", "info")
        elif choice == 1 or choice is None:
            return
        
def run():

    if not utils.is_service_installed("iptables"):
        show_firewall_installation_menu()
    
    if utils.is_service_installed("iptables"):
        show_firewall_menu()
            

        
        
