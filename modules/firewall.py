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



def manage_input_chain():
    while True:
        os.system('clear')
        utils.print_menu_name("Firewall > INPUT Chain")
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
        elif choice == 4:
            continue
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
            

        
        
