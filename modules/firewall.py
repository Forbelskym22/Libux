from simple_term_menu import TerminalMenu
import subprocess
from modules import utils
import shlex
import os

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
            choice = input(f"\n{utils.WHITE}Is your SSH running on port 22? (y/n): {utils.RESET}").lower()
            if choice == "y":
                return "22"
            elif choice == "n":
                port = input(f"{utils.WHITE}Insert your SSH port: {utils.RESET}")
                if port.isdigit():
                    return port
                utils.log("That's not a number!", "error")
            else:
                utils.log("Invalid input, type 'y' or 'n'.", "error")

    ssh_port = get_ssh_port()

    confirm = input(f"\n{utils.RED}WARNING: This will flush existing INPUT rules! Proceed? (y/n): {utils.RESET}").lower()
    
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

        if input(f"\n{utils.WHITE}Allow ICMP (Ping)? (y/n): {utils.RESET}").lower() == "y":
            subprocess.run(shlex.split("sudo iptables -A INPUT -p icmp -j ACCEPT"))
            utils.log("Ping allowed.", "success")
        
        subprocess.run(shlex.split("sudo iptables -P INPUT DROP"))
        subprocess.run(shlex.split("sudo iptables -P FORWARD DROP"))

        utils.log("Baseline applied! Policy set to DROP.", "success")
        input("\nPress Enter to return to menu...") 
    else:
        utils.log("Wizard cancelled.", "info")
        input("\nPress Enter to return...")

def show_firewall_menu():
    while True:
        os.system('clear') 
        utils.print_menu_name("Firewall Configuration (iptables)")
        
        separator = " \033[2m" + "─" * 32 + "\033[0m"
        options = [
            "[0] Default config (Wizard)",
            "[1] INPUT Chain",
            "[2] FORWARD Chain",
            "[3] NAT / MANGLE",
            separator,
            "[S] Save",
            "[X] Back"
        ]
        
        menu = TerminalMenu(options, cycle_cursor=True, clear_screen=True)
        choice = menu.show()

        if choice == 0:
            setup_secure_baseline()
        elif choice == 1:
            manage_input_chain()
        elif choice == 4:
            continue
        elif choice == 5: 
            utils.log("Save function here...", "info")
            input("\nPress Enter to continue...")
        elif choice == 6 or choice is None:
            break

def show_firewall_installation_menu():
    if not utils.is_service_installed("iptables"):
        # List with options
        options = ["Install iptables","Back to main menu"]

        # Create object of the menu
        utils.print_menu_name("Firewall isn't installed.")
        menu = TerminalMenu(options, cycle_cursor=True, clear_screen=True)

        # Render the object
        choice = menu.show()

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
            

        
        
