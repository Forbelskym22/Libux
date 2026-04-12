import os
import subprocess
from modules import utils
from .shared import get_interface_ips, get_interfaces

def get_mac(iface):
    result = subprocess.run(["cat", f"/sys/class/net/{iface}/address"], capture_output=True, text=True)
    return result.stdout.strip()

def show_interfaces(pause=True):
    os.system("clear")
    utils.print_menu_name("Interfaces")

    result = subprocess.run(["ip", "addr"], capture_output=True, text=True)

    for line in result.stdout.splitlines():
        stripped = line.strip()

        if stripped and stripped[0].isdigit():
            parts = line.split(":", 2)
            num = parts[0].strip()
            name = parts[1].strip()
            rest = parts[2] if len(parts) > 2 else ""
            rest = rest.replace("UP", f"{utils.GREEN}UP{utils.WHITE}")
            rest = rest.replace("DOWN", f"{utils.RED}DOWN{utils.WHITE}")
            print(f"  {utils.WHITE}{num}: {utils.PURPLE}{name}{utils.WHITE}:{rest}{utils.RESET}")

        elif stripped.startswith("link/"):
            parts = stripped.split()
            mac = parts[1]
            rest = " ".join(parts[2:])
            print(f"    {utils.WHITE}{parts[0]} {utils.GRAY}{mac}{utils.WHITE} {rest}{utils.RESET}")

        elif stripped.startswith("inet6"):
            parts = stripped.split()
            ip = parts[1]
            rest = " ".join(parts[2:])
            print(f"    {utils.WHITE}inet6 {utils.PINK}{ip}{utils.WHITE} {rest}{utils.RESET}")

        elif stripped.startswith("inet"):
            parts = stripped.split()
            ip = parts[1]
            rest = " ".join(parts[2:])
            print(f"    {utils.WHITE}inet {utils.PURPLE}{ip}{utils.WHITE} {rest}{utils.RESET}")

        else:
            print(f"    {utils.WHITE}{stripped}{utils.RESET}")

    if pause:
        utils.pause()


def toggle_interface():
    pass

def add_ip():
    pass

def remove_ip():
    pass

def set_dhcp():
    pass

def manage_interfaces():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Interfaces")

        options = [
            "Show",
            "Enable / Disable",
            "Add IP",
            "Set DHCP",
            "",
            "Back"
        ]

        menu = utils.create_menu(options)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_interfaces()
        elif choice == 1:
            toggle_interface()
        elif choice == 2:
            add_ip()
        elif choice == 3:
            remove_ip()
        elif choice == 4:
            set_dhcp()
        elif choice == 6 or choice is None:
            return
        
        last = choice