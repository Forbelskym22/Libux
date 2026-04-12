import os
import subprocess
import re
from modules import utils

INTERFACES_FILE = "/etc/network/interfaces"

def show_gateway(pause=True):
    os.system("clear")
    utils.print_menu_name("Default gateway")

    result = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True)
    if result.stdout.strip():
        parts = result.stdout.strip().split()
        gw = parts[2] if len(parts) >= 3 else "Unknown"
        dev = parts[4] if len(parts) >= 5 else "unknown"
        print(f"  {utils.WHITE}gateway {utils.YELLOW}{gw}{utils.WHITE} dev {utils.PURPLE}{dev}{utils.RESET}")
    else:
        utils.log("No default gateway configured.", "info")

    if pause:
        utils.pause()

def add_gateway():
    os.system("clear")
    utils.print_menu_name("Set default gateway")
    show_gateway(pause=False)

    ip = utils.ask_ip("Gateway IP")
    if not ip:
        return
    
    result = subprocess.run(["sudo", "ip", "route", "replace", "default", "via", ip], capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip(), "error")
        utils.pause()
        return

    try:
        with open(INTERFACES_FILE, "r") as f:
            content = f.read()

        if re.search(r"^\s+gateway\s+\S+", content, re.MULTILINE):
            new_content = re.sub(r"(\s+gateway\s+)\S+", rf"\g<1>{ip}", content)
        else:
            new_content = re.sub(
                r"(iface \S+ inet static[^\n]*\n(?:[ \t]+(?!gateway)[^\n]*\n)*)",
                rf"\1    gateway {ip}\n",
                content
            )

        with open(INTERFACES_FILE, "w") as f:
            f.write(new_content)

        utils.log(f"Gateway {ip} set.", "success")

    except Exception as e:
        utils.log(f"Failed to write {INTERFACES_FILE}: {e}", "error")

    utils.pause()

def remove_gateway():
    os.system("clear")
    utils.print_menu_name("Remove default gateway")
    show_gateway(pause=False)

    confirm = utils.choose(["yes", "no"], "Remove default gateway?", "error")
    if confirm != "yes":
        return

    subprocess.run(["sudo", "ip", "route", "del", "default"], capture_output=True, text=True)

    try:
        with open(INTERFACES_FILE, "r") as f:
            lines = f.readlines()

        new_lines = [l for l in lines if not re.match(r"^\s+gateway\s+\S+", l)]

        with open(INTERFACES_FILE, "w") as f:
            f.writelines(new_lines)

        utils.log("Gateway removed.", "success")

    except Exception as e:
        utils.log(f"Failed to write {INTERFACES_FILE}: {e}", "error")

    utils.pause()

def manage_gateway():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Default gateway")

        options = [
            "Show",     # 0
            "Add",      # 1
            "Remove",   # 2
            "",         # 3
            "Back"      # 4
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_gateway()
        elif choice == 1:
            add_gateway()
        elif choice == 2:
            remove_gateway()
        elif choice == 4 or choice is None:
            return
        
        last = choice
