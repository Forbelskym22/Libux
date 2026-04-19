import os
import re
import subprocess
from modules import utils
from .shared import INTERFACES_FILE

# ── Read routing table ─────────────────────────────────────────────────────────

def get_routes():
    """Returns list of dicts: {dest, gateway, iface, raw}"""
    result = subprocess.run(["ip", "route", "show"], capture_output=True, text=True)
    routes = []
    for line in result.stdout.strip().splitlines():
        parts = line.split()
        if not parts:
            continue
        dest = parts[0]
        gateway = "-"
        iface = "-"
        if "via" in parts:
            gateway = parts[parts.index("via") + 1]
        if "dev" in parts:
            iface = parts[parts.index("dev") + 1]
        routes.append({"dest": dest, "gateway": gateway, "iface": iface, "raw": line})
    return routes

def show_routes():
    os.system("clear")
    utils.print_menu_name("Routing table")
    routes = get_routes()
    if not routes:
        utils.log("No routes found.", "info")
        utils.pause()
        return
    print(f"  {utils.GRAY}{'Destination':<20}{'Gateway':<18}{'Interface'}{utils.RESET}")
    print(f"  {utils.GRAY}{'─' * 50}{utils.RESET}")
    for r in routes:
        dest = f"{utils.YELLOW}{r['dest']:<20}{utils.RESET}"
        gw   = f"{utils.WHITE}{r['gateway']:<18}{utils.RESET}"
        dev  = f"{utils.GRAY}{r['iface']}{utils.RESET}"
        print(f"  {dest}{gw}{dev}")
    print()
    utils.pause()

# ── Default gateway ────────────────────────────────────────────────────────────

def get_default_gateway():
    result = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        parts = line.split()
        if "via" in parts:
            return parts[parts.index("via") + 1]
    return None

def set_default_gateway():
    os.system("clear")
    utils.print_menu_name("Set default gateway")
    current = get_default_gateway()
    if current:
        utils.log(f"Current default gateway: {current}", "info")

    gw = utils.ask_required("New default gateway IP")
    if gw is None:
        return
    if not utils.check_ip(gw):
        utils.log("Invalid IP address.", "error")
        utils.pause()
        return

    result = subprocess.run(["sudo", "ip", "route", "replace", "default", "via", gw],
                            capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to set default gateway.", "error")
        utils.pause()
        return
    utils.log(f"Default gateway set to {gw}.", "success")

    if utils.choose(["yes", "no"], "Make persistent in /etc/network/interfaces?") == "yes":
        _persist_default_gateway(gw)

    utils.pause()

def _persist_default_gateway(gw):
    try:
        result = subprocess.run(["sudo", "cat", INTERFACES_FILE], capture_output=True, text=True)
        content = result.stdout
        if re.search(r"^\s*gateway\s+", content, re.MULTILINE):
            new_content = re.sub(r"^\s*gateway\s+\S+", f"    gateway {gw}", content,
                                 flags=re.MULTILINE)
        else:
            new_content = re.sub(r"(iface\s+\S+\s+inet\s+static[^\n]*\n)",
                                 rf"\1    gateway {gw}\n", content, count=1)
        subprocess.run(
            ["sudo", "bash", "-c", f"cat > {INTERFACES_FILE}"],
            input=new_content, text=True, capture_output=True
        )
        utils.log("Default gateway saved to /etc/network/interfaces.", "success")
    except Exception as e:
        utils.log(f"Failed to persist gateway: {e}", "error")

# ── Add route ──────────────────────────────────────────────────────────────────

def add_route():
    os.system("clear")
    utils.print_menu_name("Add static route")

    network = utils.ask_required("Network (e.g. 192.168.10.0/24)")
    if network is None:
        return

    gw = utils.ask_required("Via gateway IP")
    if gw is None:
        return
    if not utils.check_ip(gw):
        utils.log("Invalid gateway IP.", "error")
        utils.pause()
        return

    iface = utils.ask("Interface (Enter to skip)")
    if iface is None:
        return

    cmd = ["sudo", "ip", "route", "add", network, "via", gw]
    if iface:
        cmd += ["dev", iface]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to add route.", "error")
        utils.pause()
        return
    utils.log(f"Route {network} via {gw} added.", "success")

    if utils.choose(["yes", "no"], "Make persistent in /etc/network/interfaces?") == "yes":
        _persist_route_add(network, gw, iface)

    utils.pause()

def _persist_route_add(network, gw, iface):
    try:
        result = subprocess.run(["sudo", "cat", INTERFACES_FILE], capture_output=True, text=True)
        content = result.stdout
        route_line = f"    up ip route add {network} via {gw}"
        if iface:
            route_line += f" dev {iface}"
        if route_line.strip() in content:
            utils.log("Route already in /etc/network/interfaces.", "info")
            return
        # append after last iface block or at end
        new_content = content.rstrip() + f"\n{route_line}\n"
        subprocess.run(
            ["sudo", "bash", "-c", f"cat > {INTERFACES_FILE}"],
            input=new_content, text=True, capture_output=True
        )
        utils.log("Route saved to /etc/network/interfaces.", "success")
    except Exception as e:
        utils.log(f"Failed to persist route: {e}", "error")

# ── Remove route ───────────────────────────────────────────────────────────────

def remove_route():
    os.system("clear")
    utils.print_menu_name("Remove route")

    routes = get_routes()
    # exclude default — handled via set_default_gateway
    removable = [r for r in routes if r["dest"] != "default"]
    if not removable:
        utils.log("No routes to remove.", "info")
        utils.pause()
        return

    labels = [f"{r['dest']}  via {r['gateway']}  dev {r['iface']}" for r in removable]
    choice = utils.choose(labels, "Select route to remove")
    if choice is None:
        return

    idx = labels.index(choice)
    r = removable[idx]
    cmd = ["sudo", "ip", "route", "del", r["dest"]]
    if r["gateway"] != "-":
        cmd += ["via", r["gateway"]]
    if r["iface"] != "-":
        cmd += ["dev", r["iface"]]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to remove route.", "error")
        utils.pause()
        return
    utils.log(f"Route {r['dest']} removed.", "success")

    if utils.choose(["yes", "no"], "Remove from /etc/network/interfaces too?") == "yes":
        _persist_route_del(r["dest"], r["gateway"], r["iface"])

    utils.pause()

def _persist_route_del(dest, gw, iface):
    try:
        result = subprocess.run(["sudo", "cat", INTERFACES_FILE], capture_output=True, text=True)
        content = result.stdout
        new_content = re.sub(
            rf"\n\s*up ip route add {re.escape(dest)}[^\n]*", "", content
        )
        subprocess.run(
            ["sudo", "bash", "-c", f"cat > {INTERFACES_FILE}"],
            input=new_content, text=True, capture_output=True
        )
        utils.log("Route removed from /etc/network/interfaces.", "success")
    except Exception as e:
        utils.log(f"Failed to update interfaces file: {e}", "error")
