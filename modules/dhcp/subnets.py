import os
import re
import subprocess
import ipaddress
from modules import utils
from .shared import DHCP_CONFIG, DHCP_SERVICE


def get_subnets():
    subnets = []
    try:
        with open(DHCP_CONFIG, "r") as f:
            content = f.read()
        pattern = r"subnet\s+(\S+)\s+netmask\s+(\S+)\s*\{([^}]*)\}"
        for match in re.finditer(pattern, content):
            network = match.group(1)
            netmask = match.group(2)
            body = match.group(3)
            subnets.append({
                "network": network,
                "netmask": netmask,
                "body": body.strip()
            })
    except:
        pass
    return subnets


def show_subnets(pause=True):
    os.system("clear")
    utils.print_menu_name("DHCP Subnets")

    subnets = get_subnets()
    if not subnets:
        utils.log("No subnets configured.", "info")
    else:
        for s in subnets:
            print(f"  {utils.PURPLE}subnet {utils.WHITE}{s['network']} {utils.PURPLE}netmask {utils.WHITE}{s['netmask']}{utils.RESET}")
            for line in s["body"].splitlines():
                line = line.strip()
                if line:
                    print(f"    {utils.YELLOW}{line}{utils.RESET}")
            print()

    if pause:
        utils.pause()


def parse_network(cidr):
    try:
        net = ipaddress.ip_network(cidr, strict=False)
        return str(net.network_address), str(net.netmask)
    except ValueError:
        return None, None


def add_subnet():
    os.system("clear")
    utils.print_menu_name("Add subnet")
    show_subnets(pause=False)

    while True:
        cidr = utils.ask_required("Network (e.g. 192.168.1.0/24)")
        if cidr is None:
            return
        network, netmask = parse_network(cidr)
        if network:
            break
        utils.log("Invalid network address.", "error")

    while True:
        range_start = utils.ask_required("Range start (e.g. 192.168.1.100)")
        if range_start is None:
            return
        if utils.check_ip(range_start):
            break
        utils.log("Invalid IP address.", "error")

    while True:
        range_end = utils.ask_required("Range end (e.g. 192.168.1.200)")
        if range_end is None:
            return
        if utils.check_ip(range_end):
            break
        utils.log("Invalid IP address.", "error")

    gateway = utils.ask("Gateway")
    dns = utils.ask("DNS server")

    block = f"\nsubnet {network} netmask {netmask} {{\n"
    block += f"    range {range_start} {range_end};\n"
    if gateway:
        block += f"    option routers {gateway};\n"
    if dns:
        block += f"    option domain-name-servers {dns};\n"
    block += "}\n"

    try:
        with open(DHCP_CONFIG, "a") as f:
            f.write(block)
        utils.log(f"Subnet {network}/{netmask} added.", "success")
    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        utils.pause()
        return

    utils.log("Restarting DHCP service...", "info")
    try:
        subprocess.run(["sudo", "systemctl", "reset-failed", DHCP_SERVICE], capture_output=True, text=True)
        result = subprocess.run(["sudo", "systemctl", "restart", DHCP_SERVICE], capture_output=True, text=True)
        if result.returncode == 0:
            utils.log("DHCP service restarted.", "success")
        else:
            utils.log("Service failed to restart. Try manually: systemctl restart isc-dhcp-server", "error")
    except KeyboardInterrupt:
        pass

    utils.pause()


def remove_subnet():
    os.system("clear")
    utils.print_menu_name("Remove subnet")

    subnets = get_subnets()
    if not subnets:
        utils.log("No subnets to remove.", "error")
        utils.pause()
        return

    options = [f"{s['network']} / {s['netmask']}" for s in subnets]
    choice = utils.choose(options, "Select subnet to remove")
    if choice is None:
        return

    idx = options.index(choice)
    selected = subnets[idx]

    confirm = utils.choose(["yes", "no"], f"Remove subnet {selected['network']}?", "error")
    if confirm != "yes":
        return

    try:
        with open(DHCP_CONFIG, "r") as f:
            content = f.read()

        pattern = rf"subnet\s+{re.escape(selected['network'])}\s+netmask\s+{re.escape(selected['netmask'])}\s*\{{[^}}]*\}}\n?"
        new_content = re.sub(pattern, "", content)

        with open(DHCP_CONFIG, "w") as f:
            f.write(new_content)

        utils.log(f"Subnet {selected['network']} removed.", "success")

    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        utils.pause()
        return

    utils.log("Restarting DHCP service...", "info")
    try:
        subprocess.run(["sudo", "systemctl", "reset-failed", DHCP_SERVICE], capture_output=True, text=True)
        result = subprocess.run(["sudo", "systemctl", "restart", DHCP_SERVICE], capture_output=True, text=True)
        if result.returncode == 0:
            utils.log("DHCP service restarted.", "success")
        else:
            utils.log("No subnets left — service stopped.", "info")
    except KeyboardInterrupt:
        pass

    utils.pause()


def manage_subnets():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Subnets")

        options = [
            "Show",     # 0
            "Add",      # 1
            "Remove",   # 2
            "",         # 3
            "Back",     # 4
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_subnets()
        elif choice == 1:
            add_subnet()
        elif choice == 2:
            remove_subnet()
        elif choice == 4 or choice is None:
            return

        last = choice
