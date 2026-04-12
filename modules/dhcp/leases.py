import os
import re
from modules import utils
from .shared import DHCP_CONFIG, LEASES_FILE, restart_dhcp


def get_leases():
    leases = []
    try:
        with open(LEASES_FILE, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return leases

    for match in re.finditer(
        r"lease\s+(\S+)\s*\{([^}]*)\}", content
    ):
        ip = match.group(1)
        body = match.group(2)

        lease = {"ip": ip}

        m = re.search(r"starts\s+\d+\s+([^;]+);", body)
        if m:
            lease["starts"] = m.group(1).strip()

        m = re.search(r"ends\s+\d+\s+([^;]+);", body)
        if m:
            lease["ends"] = m.group(1).strip()

        m = re.search(r"hardware\s+ethernet\s+([^;]+);", body)
        if m:
            lease["mac"] = m.group(1).strip()

        m = re.search(r"client-hostname\s+\"([^\"]*)\";", body)
        if m:
            lease["hostname"] = m.group(1).strip()

        m = re.search(r"binding\s+state\s+(\S+);", body)
        if m:
            lease["state"] = m.group(1).strip()

        leases.append(lease)

    return leases


def show_leases():
    os.system("clear")
    utils.print_menu_name("DHCP Leases")

    leases = get_leases()
    if not leases:
        utils.log("No leases found.", "info")
        utils.pause()
        return

    active = [l for l in leases if l.get("state") == "active"]
    other = [l for l in leases if l.get("state") != "active"]

    if active:
        utils.log(f"Active leases ({len(active)}):", "success")
        print()
        for l in active:
            _print_lease(l)

    if other:
        utils.log(f"Expired/free leases ({len(other)}):", "info")
        print()
        for l in other:
            _print_lease(l)

    utils.pause()


def _print_lease(l):
    ip = l.get("ip", "?")
    mac = l.get("mac", "?")
    hostname = l.get("hostname", "")
    state = l.get("state", "?")
    ends = l.get("ends", "?")

    state_color = utils.GREEN if state == "active" else utils.GRAY

    name_str = f" ({utils.YELLOW}{hostname}{utils.RESET})" if hostname else ""
    print(f"  {utils.WHITE}{ip}{utils.RESET}  {utils.PURPLE}{mac}{utils.RESET}"
          f"{name_str}  {state_color}{state}{utils.RESET}"
          f"  {utils.GRAY}expires {ends}{utils.RESET}")


# --- Reservations (host bloky v dhcpd.conf) ---

def get_reservations():
    reservations = []
    try:
        with open(DHCP_CONFIG, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return reservations

    for match in re.finditer(
        r"host\s+(\S+)\s*\{([^}]*)\}", content
    ):
        name = match.group(1)
        body = match.group(2)

        res = {"name": name}

        m = re.search(r"hardware\s+ethernet\s+([^;]+);", body)
        if m:
            res["mac"] = m.group(1).strip()

        m = re.search(r"fixed-address\s+([^;]+);", body)
        if m:
            res["ip"] = m.group(1).strip()

        reservations.append(res)

    return reservations


def show_reservations():
    os.system("clear")
    utils.print_menu_name("DHCP Reservations")

    reservations = get_reservations()
    if not reservations:
        utils.log("No reservations configured.", "info")
    else:
        for r in reservations:
            print(f"  {utils.YELLOW}{r['name']}{utils.RESET}"
                  f"  {utils.PURPLE}{r.get('mac', '?')}{utils.RESET}"
                  f"  {utils.WHITE}{r.get('ip', '?')}{utils.RESET}")
        print()

    utils.pause()


def _parse_mac(mac):
    """Validuje MAC a vrátí v unified formátu AA:BB:CC:DD:EE:FF. None pokud neplatná."""
    # odstraň oddělovače a zkontroluj 12 hex znaků
    raw = mac.replace(":", "").replace(".", "").replace("-", "")
    if not re.match(r"^[0-9a-fA-F]{12}$", raw):
        return None
    # sestav XX:XX:XX:XX:XX:XX
    return ":".join(raw[i:i+2] for i in range(0, 12, 2)).lower()


def add_reservation():
    os.system("clear")
    utils.print_menu_name("Add Reservation")

    # název
    name = utils.ask_required("Hostname (e.g. pc-ucebna)")
    if name is None:
        return

    # MAC
    while True:
        raw_mac = utils.ask_required("MAC address (e.g. AA:BB:CC:DD:EE:FF)")
        if raw_mac is None:
            return
        mac = _parse_mac(raw_mac)
        if mac:
            break
        utils.log("Invalid MAC address.", "error")

    # IP
    while True:
        ip = utils.ask_required("IP address (e.g. 10.10.10.50)")
        if ip is None:
            return
        if utils.check_ip(ip):
            break
        utils.log("Invalid IP address.", "error")

    block = f"\nhost {name} {{\n"
    block += f"    hardware ethernet {mac};\n"
    block += f"    fixed-address {ip};\n"
    block += "}\n"

    try:
        with open(DHCP_CONFIG, "a") as f:
            f.write(block)
        utils.log(f"Reservation {name} ({mac} -> {ip}) added.", "success")
    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        utils.pause()
        return

    utils.log("Restarting DHCP service...", "info")
    restart_dhcp()
    utils.pause()


def remove_reservation():
    os.system("clear")
    utils.print_menu_name("Remove Reservation")

    reservations = get_reservations()
    if not reservations:
        utils.log("No reservations to remove.", "info")
        utils.pause()
        return

    options = [f"{r['name']} — {r.get('mac', '?')} -> {r.get('ip', '?')}" for r in reservations]
    choice = utils.choose(options, "Select reservation to remove")
    if choice is None:
        return

    idx = options.index(choice)
    selected = reservations[idx]

    confirm = utils.choose(
        ["yes", "no"],
        f"Remove reservation {selected['name']}?", "error"
    )
    if confirm != "yes":
        return

    try:
        with open(DHCP_CONFIG, "r") as f:
            content = f.read()

        pattern = rf"\n?host\s+{re.escape(selected['name'])}\s*\{{[^}}]*\}}\n?"
        new_content = re.sub(pattern, "\n", content)

        with open(DHCP_CONFIG, "w") as f:
            f.write(new_content)

        utils.log(f"Reservation {selected['name']} removed.", "success")
    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        utils.pause()
        return

    utils.log("Restarting DHCP service...", "info")
    restart_dhcp()
    utils.pause()


def manage_leases():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("DHCP Leases & Reservations")

        options = [
            "Show leases",          # 0
            "",                     # 1
            "Show reservations",    # 2
            "Add reservation",      # 3
            "Remove reservation",   # 4
            "",                     # 5
            "Back",                 # 6
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_leases()
        elif choice == 2:
            show_reservations()
        elif choice == 3:
            add_reservation()
        elif choice == 4:
            remove_reservation()
        elif choice == 6 or choice is None:
            return

        last = choice
