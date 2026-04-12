import os
import re
import subprocess
import ipaddress
from modules import utils
from .shared import DHCP_CONFIG, DHCP_DEFAULTS, restart_dhcp


def get_subnets():
    subnets = []
    try:
        with open(DHCP_CONFIG, "r") as f:
            content = f.read()
        pattern = r"subnet\s+(\S+)\s+netmask\s+(\S+)\s*\{([^}]*)\}"
        for match in re.finditer(pattern, content):
            subnets.append({
                "network": match.group(1),
                "netmask": match.group(2),
                "body": match.group(3).strip()
            })
    except FileNotFoundError:
        pass
    return subnets


def get_dhcp_interfaces():
    """Vrátí seznam interfaců z INTERFACESv4."""
    try:
        with open(DHCP_DEFAULTS, "r") as f:
            content = f.read()
        match = re.search(r'INTERFACESv4="([^"]*)"', content)
        if match and match.group(1).strip():
            return match.group(1).strip().split()
    except FileNotFoundError:
        pass
    return []


def add_dhcp_interface(iface):
    """Přidá interface do INTERFACESv4 pokud tam ještě není."""
    current = get_dhcp_interfaces()
    if iface in current:
        return

    current.append(iface)
    new_value = " ".join(current)

    try:
        with open(DHCP_DEFAULTS, "r") as f:
            content = f.read()
        content = re.sub(
            r'INTERFACESv4="[^"]*"',
            f'INTERFACESv4="{new_value}"',
            content
        )
        with open(DHCP_DEFAULTS, "w") as f:
            f.write(content)
    except Exception as e:
        utils.log(f"Failed to update interfaces: {e}", "error")


def remove_dhcp_interface(iface):
    """Odebere interface z INTERFACESv4."""
    current = get_dhcp_interfaces()
    if iface not in current:
        return

    current.remove(iface)
    new_value = " ".join(current)

    try:
        with open(DHCP_DEFAULTS, "r") as f:
            content = f.read()
        content = re.sub(
            r'INTERFACESv4="[^"]*"',
            f'INTERFACESv4="{new_value}"',
            content
        )
        with open(DHCP_DEFAULTS, "w") as f:
            f.write(content)
    except Exception as e:
        utils.log(f"Failed to update interfaces: {e}", "error")


def get_interface_network(iface):
    """Zjistí IP a síť daného interface."""
    result = subprocess.run(
        ["ip", "-o", "-4", "addr", "show", iface],
        capture_output=True, text=True
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None

    match = re.search(r"inet\s+(\S+)", result.stdout)
    if not match:
        return None

    try:
        return ipaddress.ip_interface(match.group(1))
    except ValueError:
        return None


def show_subnets(pause=True):
    os.system("clear")
    utils.print_menu_name("DHCP Subnets")

    subnets = get_subnets()
    if not subnets:
        utils.log("No subnets configured.", "info")
    else:
        for s in subnets:
            print(f"  {utils.PURPLE}subnet {utils.WHITE}{s['network']} "
                  f"{utils.PURPLE}netmask {utils.WHITE}{s['netmask']}{utils.RESET}")
            for line in s["body"].splitlines():
                line = line.strip()
                if line:
                    print(f"    {utils.YELLOW}{line}{utils.RESET}")
            print()

    if pause:
        utils.pause()


def add_subnet():
    os.system("clear")
    utils.print_menu_name("Add Subnet")

    # vyber interface
    iface = utils.pick_interface("DHCP interface", exclude=["lo"])
    if iface is None:
        return

    # detekuj síť
    iface_net = get_interface_network(iface)
    if not iface_net:
        utils.log(f"Interface {iface} has no IP address. Set one first.", "error")
        utils.pause()
        return

    net = iface_net.network

    utils.log(f"Detected: {net}", "success")
    print()

    # range start
    while True:
        range_start = utils.ask_required(f"Range start (e.g. {net.network_address + 100})")
        if range_start is None:
            return
        try:
            start_ip = ipaddress.ip_address(range_start)
            if start_ip in net:
                break
            utils.log(f"Address is not in {net}.", "error")
        except ValueError:
            utils.log("Invalid IP address.", "error")

    # range end
    while True:
        range_end = utils.ask_required(f"Range end (e.g. {net.network_address + 200})")
        if range_end is None:
            return
        try:
            end_ip = ipaddress.ip_address(range_end)
            if end_ip not in net:
                utils.log(f"Address is not in {net}.", "error")
            elif end_ip <= start_ip:
                utils.log("Range end must be greater than range start.", "error")
            else:
                break
        except ValueError:
            utils.log("Invalid IP address.", "error")

    # gateway
    gw_choice = utils.choose(
        [f"Use {iface_net.ip} (this server)", "Custom", "None (LAN only)"],
        "Gateway"
    )
    if gw_choice is None:
        return
    if "this server" in gw_choice:
        gateway = str(iface_net.ip)
    elif gw_choice == "Custom":
        gateway = utils.ask_required("Gateway IP")
        if gateway is None:
            return
        if not utils.check_ip(gateway):
            utils.log("Invalid IP, skipping gateway.", "error")
            gateway = None
    else:
        gateway = None

    # DNS
    dns = utils.ask("DNS server")
    if dns and not utils.check_ip(dns):
        utils.log("Invalid DNS, skipping.", "error")
        dns = None

    # lease time
    lease_time = utils.ask("Lease time in seconds (default: 600)")
    if lease_time and not lease_time.isdigit():
        utils.log("Invalid number, using default 600.", "error")
        lease_time = None

    max_lease = utils.ask("Max lease time in seconds (default: 7200)")
    if max_lease and not max_lease.isdigit():
        utils.log("Invalid number, using default 7200.", "error")
        max_lease = None

    # sestav blok
    network = str(net.network_address)
    netmask = str(net.netmask)

    block = f"\nsubnet {network} netmask {netmask} {{\n"
    block += f"    range {range_start} {range_end};\n"
    if gateway:
        block += f"    option routers {gateway};\n"
    if dns:
        block += f"    option domain-name-servers {dns};\n"
    if lease_time:
        block += f"    default-lease-time {lease_time};\n"
    if max_lease:
        block += f"    max-lease-time {max_lease};\n"
    block += "}\n"

    try:
        with open(DHCP_CONFIG, "a") as f:
            f.write(block)
        utils.log(f"Subnet {net} added.", "success")
    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        utils.pause()
        return

    # přidej interface do INTERFACESv4
    add_dhcp_interface(iface)

    utils.log("Restarting DHCP service...", "info")
    restart_dhcp()
    utils.pause()


def _parse_subnet_body(body):
    """Parsuje tělo subnet bloku na jednotlivé hodnoty."""
    values = {}
    m = re.search(r"range\s+(\S+)\s+(\S+);", body)
    if m:
        values["range_start"] = m.group(1)
        values["range_end"] = m.group(2)
    m = re.search(r"option\s+routers\s+(\S+);", body)
    if m:
        values["gateway"] = m.group(1)
    m = re.search(r"option\s+domain-name-servers\s+(\S+);", body)
    if m:
        values["dns"] = m.group(1)
    m = re.search(r"default-lease-time\s+(\d+);", body)
    if m:
        values["lease_time"] = m.group(1)
    m = re.search(r"max-lease-time\s+(\d+);", body)
    if m:
        values["max_lease"] = m.group(1)
    return values


def edit_subnet():
    os.system("clear")
    utils.print_menu_name("Edit Subnet")

    subnets = get_subnets()
    if not subnets:
        utils.log("No subnets to edit.", "info")
        utils.pause()
        return

    options = [f"{s['network']} / {s['netmask']}" for s in subnets]
    choice = utils.choose(options, "Select subnet to edit")
    if choice is None:
        return

    idx = options.index(choice)
    selected = subnets[idx]
    current = _parse_subnet_body(selected["body"])

    try:
        net = ipaddress.ip_network(
            f"{selected['network']}/{selected['netmask']}", strict=False
        )
    except ValueError:
        utils.log("Cannot parse subnet.", "error")
        utils.pause()
        return

    utils.log(f"Editing {net} — Enter to keep current value", "info")
    print()

    # range start
    cur_start = current.get("range_start", "")
    while True:
        raw = utils.ask(f"Range start (current: {cur_start})")
        if raw is None:
            return
        if not raw:
            range_start = cur_start
            break
        try:
            ip = ipaddress.ip_address(raw)
            if ip in net:
                range_start = raw
                break
            utils.log(f"Address is not in {net}.", "error")
        except ValueError:
            utils.log("Invalid IP address.", "error")

    # range end
    cur_end = current.get("range_end", "")
    while True:
        raw = utils.ask(f"Range end (current: {cur_end})")
        if raw is None:
            return
        if not raw:
            range_end = cur_end
            break
        try:
            ip = ipaddress.ip_address(raw)
            if ip not in net:
                utils.log(f"Address is not in {net}.", "error")
            elif ip <= ipaddress.ip_address(range_start):
                utils.log("Range end must be greater than range start.", "error")
            else:
                range_end = raw
                break
        except ValueError:
            utils.log("Invalid IP address.", "error")

    # gateway
    cur_gw = current.get("gateway", "")
    while True:
        raw = utils.ask(f"Gateway (current: {cur_gw or 'none'})")
        if raw is None:
            return
        if not raw:
            gateway = cur_gw
            break
        if utils.check_ip(raw):
            gateway = raw
            break
        utils.log("Invalid IP address.", "error")

    # DNS
    cur_dns = current.get("dns", "")
    while True:
        raw = utils.ask(f"DNS server (current: {cur_dns or 'none'})")
        if raw is None:
            return
        if not raw:
            dns = cur_dns
            break
        if utils.check_ip(raw):
            dns = raw
            break
        utils.log("Invalid IP address.", "error")

    # lease time
    cur_lease = current.get("lease_time", "")
    while True:
        raw = utils.ask(f"Lease time in seconds (current: {cur_lease or 'global default'})")
        if raw is None:
            return
        if not raw:
            lease_time = cur_lease
            break
        if raw.isdigit():
            lease_time = raw
            break
        utils.log("Invalid number.", "error")

    cur_max = current.get("max_lease", "")
    while True:
        raw = utils.ask(f"Max lease time in seconds (current: {cur_max or 'global default'})")
        if raw is None:
            return
        if not raw:
            max_lease = cur_max
            break
        if raw.isdigit():
            max_lease = raw
            break
        utils.log("Invalid number.", "error")

    # sestav nový blok
    network = selected["network"]
    netmask = selected["netmask"]

    block = f"subnet {network} netmask {netmask} {{\n"
    block += f"    range {range_start} {range_end};\n"
    if gateway:
        block += f"    option routers {gateway};\n"
    if dns:
        block += f"    option domain-name-servers {dns};\n"
    if lease_time:
        block += f"    default-lease-time {lease_time};\n"
    if max_lease:
        block += f"    max-lease-time {max_lease};\n"
    block += "}"

    # nahraď starý blok novým
    try:
        with open(DHCP_CONFIG, "r") as f:
            content = f.read()

        pattern = (
            rf"subnet\s+{re.escape(network)}"
            rf"\s+netmask\s+{re.escape(netmask)}"
            rf"\s*\{{[^}}]*\}}"
        )
        new_content = re.sub(pattern, block, content)

        with open(DHCP_CONFIG, "w") as f:
            f.write(new_content)

        utils.log(f"Subnet {network} updated.", "success")
    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        utils.pause()
        return

    utils.log("Restarting DHCP service...", "info")
    restart_dhcp()
    utils.pause()


def remove_subnet():
    os.system("clear")
    utils.print_menu_name("Remove Subnet")

    subnets = get_subnets()
    if not subnets:
        utils.log("No subnets to remove.", "info")
        utils.pause()
        return

    options = [f"{s['network']} / {s['netmask']}" for s in subnets]
    choice = utils.choose(options, "Select subnet to remove")
    if choice is None:
        return

    idx = options.index(choice)
    selected = subnets[idx]

    confirm = utils.choose(
        ["yes", "no"],
        f"Remove subnet {selected['network']}?", "error"
    )
    if confirm != "yes":
        return

    try:
        with open(DHCP_CONFIG, "r") as f:
            content = f.read()

        pattern = (
            rf"\n?subnet\s+{re.escape(selected['network'])}"
            rf"\s+netmask\s+{re.escape(selected['netmask'])}"
            rf"\s*\{{[^}}]*\}}\n?"
        )
        new_content = re.sub(pattern, "\n", content)

        with open(DHCP_CONFIG, "w") as f:
            f.write(new_content)

        utils.log(f"Subnet {selected['network']} removed.", "success")
    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        utils.pause()
        return

    utils.log("Restarting DHCP service...", "info")
    restart_dhcp()
    utils.pause()


def manage_subnets():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Subnets")

        options = [
            "Show",     # 0
            "Add",      # 1
            "Edit",     # 2
            "Remove",   # 3
            "",         # 4
            "Back",     # 5
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_subnets()
        elif choice == 1:
            add_subnet()
        elif choice == 2:
            edit_subnet()
        elif choice == 3:
            remove_subnet()
        elif choice == 5 or choice is None:
            return

        last = choice
