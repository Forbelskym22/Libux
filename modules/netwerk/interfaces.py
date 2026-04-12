import os
import subprocess
import re
from modules import utils
from .shared import get_interface_ips, get_interfaces, ask_interface_ip

INTERFACES_FILE="/etc/network/interfaces"

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
    os.system("clear")
    utils.print_menu_name("Add IP address")
    show_interfaces(pause=False)

    iface = utils.pick_interface()
    if iface is None:
        return

    ip = ask_interface_ip()
    if not ip:
        return
    
    try:
        with open(INTERFACES_FILE, "r") as f:
            content = f.read()

        pattern = rf"(iface {re.escape(iface)} inet static[^\n]*\n(?:[ \t]+[^\n]*\n)*)"
        match = re.search(pattern, content)

        if match:
            block = match.group(1)
            label_count = len(re.findall(r"up\s+/sbin/ip addr add", block))
            label = f"{iface}:{label_count}"

            new_lines = (
                f"    up   /sbin/ip addr add {ip} dev $IFACE label {label}\n"
                f"    down /sbin/ip addr del {ip} dev $IFACE label {label}\n"
            )
            new_block = block.rstrip("\n") + "\n" + new_lines
            new_content = content[:match.start()] + new_block + content[match.end():]
        else:
            new_content = content.rstrip() + f"\n\niface {iface} inet static\n    address {ip}\n"

        with open(INTERFACES_FILE, "w") as f:
            f.write(new_content)

        utils.log(f"{ip} added to {iface}.", "success")

    except Exception as e:
        utils.log(f"Failed to write {INTERFACES_FILE}: {e}", "error")
        utils.pause()
        return

    utils.log("Restarting networking service...", "info")
    subprocess.run(["sudo", "systemctl", "restart", "networking"])
    utils.pause()


def remove_ip():
    os.system("clear")
    utils.print_menu_name("Add IP address")
    show_interfaces(pause=False)

    iface = utils.pick_interface()
    if iface is None:
        return
    
    try:
        with open(INTERFACES_FILE, "r") as f:
            content = f.read()

        pattern = rf"(iface {re.escape(iface)} inet static[^\n]*\n(?:[ \t]+[^\n]*\n)*)"
        match = re.search(pattern, content)

        if not match:
            utils.log(f"No static config found for {iface}.", "error")
            utils.pause()
            return

        block = match.group(1)

        address_match = re.search(r"address\s+(\S+)", block)
        primary_ip = address_match.group(1) if address_match else None

        extra_ips = re.findall(r"up\s+/sbin/ip addr add (\S+) dev", block)

        all_ips = []
        if primary_ip:
            all_ips.append(primary_ip)
        all_ips.extend(extra_ips)

        if not all_ips:
            utils.log(f"No IP addresses found for {iface}.", "error")
            utils.pause()
            return

        ip = utils.choose(all_ips, f"Select IP to remove from {iface}")
        if ip is None:
            return

        if ip == primary_ip:
            if extra_ips:
                new_primary = extra_ips[0]
                new_block = block
                new_block = re.sub(r"address\s+\S+", f"address {new_primary}", new_block)
                new_block = re.sub(
                    rf"[ \t]+up\s+/sbin/ip addr add {re.escape(new_primary)} dev \$IFACE label \S+\n"
                    rf"[ \t]+down\s+/sbin/ip addr del {re.escape(new_primary)} dev \$IFACE label \S+\n",
                    "", new_block
                )
            else:
                new_block = ""
        else:
            new_block = re.sub(
                rf"[ \t]+up\s+/sbin/ip addr add {re.escape(ip)} dev \$IFACE label \S+\n"
                rf"[ \t]+down\s+/sbin/ip addr del {re.escape(ip)} dev \$IFACE label \S+\n",
                "", block
            )

        new_content = content[:match.start()] + new_block + content[match.end():]

        with open(INTERFACES_FILE, "w") as f:
            f.write(new_content)

        utils.log(f"{ip} removed from {iface}.", "success")

    except Exception as e:
        utils.log(f"Failed to write {INTERFACES_FILE}: {e}", "error")
        utils.pause()
        return

    utils.log("Restarting networking service...", "info")
    subprocess.run(["sudo", "systemctl", "restart", "networking"])
    utils.pause()

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
            "Remove IP",
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