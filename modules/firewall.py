from simple_term_menu import TerminalMenu
import subprocess
import shlex
import os
from modules import utils
from modules.fw_shared import discard_changes, save_rules, edit_rules, ask, ask_required, show_chain
from modules.fw_input import manage_input_chain
from modules.fw_output import manage_output_chain
from modules.fw_forward import manage_forward_chain
from modules.fw_nat import manage_prerouting, manage_postrouting




def show_firewall():
    os.system('clear')
    utils.print_menu_name("Firewall rules")

    for chain in ["INPUT", "FORWARD", "OUTPUT"]:
        show_chain(chain, clear=False, pause=False)

    print(f"{utils.PURPLE}--- NAT table ---{utils.RESET}\n")

    for chain in ["PREROUTING", "POSTROUTING", "INPUT", "OUTPUT"]:
        show_chain(chain, table="nat", clear=False, pause=False)

    try:
        input("\nPress Enter to return to menu...")
    except KeyboardInterrupt:
        pass



def setup_secure_baseline():
    os.system('clear')
    utils.print_menu_name("Secure Baseline Wizard")
    utils.log("This will reset INPUT chain and set a secure 'DROP' policy.", "info")

    def get_ssh_port():
        while True:
            try:
                port = ask_required("Insert your SSH port")
            except KeyboardInterrupt:
                return None
            if utils.check_port(port):
                return port
            utils.log("That's not a port number!", "error")

    def get_ssh_ip():
        while True:
            try:
                ip = ask("Insert your SSH source IP")
            except KeyboardInterrupt:
                return None
            if not ip: return None  # Enter to skip
            if utils.check_ip(ip): return ip
            utils.log("That's not an ip address!", "error")

    
    allow_ssh = utils.choose(["yes","no"], "Do you want to allow ssh to your machine?")
    if allow_ssh is None:
        return  
    if allow_ssh == "yes":
        ssh_port = get_ssh_port()
        ssh_ip = get_ssh_ip()

    try:
        confirm = utils.choose(["yes","no"], "WARNING: This will flush existing INPUT rules! Proceed? (y/n)", "error")
    except KeyboardInterrupt:
        utils.log("Wizard cancelled.", "info")
        return

    if confirm == 'yes':
        utils.log("Applying core rules...", "info")

        core_commands = [
            "sudo iptables -F INPUT",
            "sudo iptables -A INPUT -i lo -j ACCEPT",
            "sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
        ]

        if allow_ssh == "yes" and ssh_port:
            if ssh_ip:
                core_commands.append(f"sudo iptables -A INPUT -s {ssh_ip} -p tcp --dport {ssh_port} -j ACCEPT")
            else:
                core_commands.append(f"sudo iptables -A INPUT -p tcp --dport {ssh_port} -j ACCEPT")
        

        try:
            allow_icmp = utils.choose(["yes","no"], "Allow ICMP?")
            if allow_icmp == "yes":
                icmp_ip = ask("Select an source IP address to allow ICMP from")
                if icmp_ip:
                    core_commands.append(f"sudo iptables -A INPUT -s {icmp_ip} -p icmp -j ACCEPT")
                else:
                    core_commands.append("sudo iptables -A INPUT -p icmp -j ACCEPT")
                utils.log("Ping allowed.", "success")
        except KeyboardInterrupt:
            pass

        for cmd in core_commands:
            subprocess.run(shlex.split(cmd))

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
    last = 0
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall Configuration (iptables)")

        options = [
            "Default config (Wizard)",              # 0
            "INPUT Chain",                          # 1
            "OUTPUT Chain",                         # 2
            "FORWARD Chain",                        # 3
            "PREROUTING (DNAT / Port forwarding)",  # 4
            "POSTROUTING (MASQUERADE)",             # 5
            "",                                     # 6
            "Show",                                 # 7
            "Edit",                                 # 8
            "",                                     # 9
            "Save",                                 # 10
            "Discard",                              # 11
            "Back"                                  # 12
        ]

        menu = TerminalMenu(options,cursor_index=last, cycle_cursor=True, clear_screen=False, skip_empty_entries=True, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            setup_secure_baseline()
        elif choice == 1:
            manage_input_chain()
        elif choice == 2:
            manage_output_chain()
        elif choice == 3:
            manage_forward_chain()
        elif choice == 4:
            manage_prerouting()
        elif choice == 5:
            manage_postrouting()
        elif choice == 7:
            show_firewall()
        elif choice == 8:
            edit_rules()
        elif choice == 10:
            save_rules()
            
        elif choice == 11:
            discard_changes()
        elif choice == 12 or choice is None:
            break

        last = choice


def show_firewall_installation_menu():
    if not utils.is_service_installed("iptables"):
        options = ["Install iptables", "Back to main menu"]

        utils.print_menu_name("Firewall isn't installed.")
        menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice == 0:
            utils.log("Starting an installation of iptables...", "info")
            subprocess.run(["sudo", "apt", "update"])
            subprocess.run(["sudo", "apt", "install", "iptables", "-y"])

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
