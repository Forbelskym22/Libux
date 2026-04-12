import os
import re
import subprocess
from modules import utils
from .shared import ask_interface_ip

INTERFACES_FILE = "/etc/network/interfaces"

def get_vlan_interfaces():
    result = subprocess.run(["ip", "-o", "link", "show", "type", "vlan"], capture_output=True, text=True)
    vlans = []
    for line in result.stdout.splitlines():
        parts = line.split()
        name = parts[1].strip(":").split("@")[0]
        vlans.append(name)
    return vlans

def show_vlans(pause=True):
    os.system("clear")
    utils.print_menu_name("VLANs")

    vlans = get_vlan_interfaces()
    if not vlans:
        utils.log("No VLAN interfaces configured.", "info")
    else:
        result = subprocess.run(["ip","addr"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped and stripped[0].isdigit():
                name = line.split(":")[1].strip()
                if name not in vlans:
                    continue
                rest = line.split(":", 2)[2] if len(line.split(":", 2)) > 2 else ""
                rest = rest.replace("UP", f"{utils.GREEN}UP{utils.WHITE}")
                rest = rest.replace("DOWN", f"{utils.RED}DOWN{utils.WHITE}")
                print(f"  {utils.WHITE}{line.split(':')[0].strip()}: {utils.PURPLE}{name}{utils.WHITE}:{rest}{utils.RESET}")
            elif stripped.startswith("inet") and any(v in result.stdout.splitlines()[result.stdout.splitlines().index(line)-1] for v in vlans):
                parts = stripped.split()
                ip = parts[1]
                rest = " ".join(parts[2:])
                print(f"    {utils.WHITE}inet {utils.YELLOW}{ip}{utils.WHITE} {rest}{utils.RESET}")

    if pause:
        utils.pause()


def add_vlan():
    os.system("clear")
    utils.print_menu_name("Add VLAN")

    parent = utils.pick_interface("parent interface")
    if parent is None:
        return

    vlan_id = utils.ask_required("VLAN ID (1-4094)")
    if vlan_id is None:
        return
    if not vlan_id.isdigit() or not (1 <= int(vlan_id) <= 4094):
        utils.log("Invalid VLAN ID.", "error")
        utils.pause()
        return

    iface_name = f"{parent}.{vlan_id}"

    ip = ask_interface_ip()
    if not ip:
        return

    result = subprocess.run(["sudo", "ip", "link", "add", "link", parent, "name", iface_name, "type", "vlan", "id", vlan_id], capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip(), "error")
        utils.pause()
        return

    subprocess.run(["sudo", "ip", "link", "set", iface_name, "up"], capture_output=True, text=True)
    subprocess.run(["sudo", "ip", "addr", "add", ip, "dev", iface_name], capture_output=True, text=True)

    try:
        with open(INTERFACES_FILE, "r") as f:
            content = f.read()

        block = (
            f"\nauto {iface_name}\n"
            f"iface {iface_name} inet static\n"
            f"    address {ip}\n"
            f"    vlan-raw-device {parent}\n"
        )

        if f"iface {iface_name}" not in content:
            with open(INTERFACES_FILE, "a") as f:
                f.write(block)

        utils.log(f"VLAN {vlan_id} ({iface_name}) created with {ip}.", "success")

    except Exception as e:
        utils.log(f"Failed to write {INTERFACES_FILE}: {e}", "error")

    utils.pause()

def remove_vlan():
    os.system("clear")
    utils.print_menu_name("Remove VLAN")

    vlans = get_vlan_interfaces()
    if not vlans:
        utils.log("No VLAN interfaces to remove.", "error")
        utils.pause()
        return

    vlan = utils.choose(vlans, "Select VLAN to remove")
    if vlan is None:
        return

    confirm = utils.choose(["yes", "no"], f"Remove {vlan}?", "error")
    if confirm != "yes":
        return

    subprocess.run(["sudo", "ip", "link", "set", vlan, "down"], capture_output=True, text=True)
    result = subprocess.run(["sudo", "ip", "link", "delete", vlan], capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip(), "error")
        utils.pause()
        return
    
    try:
        with open(INTERFACES_FILE, "r") as f:
            content = f.read()

        pattern = rf"(?:auto {re.escape(vlan)}\n)?iface {re.escape(vlan)} inet static[^\n]*\n(?:[ \t]+[^\n]*\n)*"
        new_content = re.sub(pattern, "", content)

        with open(INTERFACES_FILE, "w") as f:
            f.write(new_content)

        utils.log(f"{vlan} removed.", "success")

    except Exception as e:
        utils.log(f"Failed to write {INTERFACES_FILE}: {e}", "error")

    utils.pause()


def manage_vlan():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("VLAN")

        options = [
            "Show",             # 0
            "Add",              # 1
            "Remove",           # 2
            "",                 # 3
            "Back"              # 4
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_vlans()
        elif choice == 1:
            add_vlan()
        elif choice == 2:
            remove_vlan()
        elif choice == 4 or choice is None:
            return
        
        last = choice
