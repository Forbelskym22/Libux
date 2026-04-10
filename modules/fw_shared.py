from simple_term_menu import TerminalMenu
import subprocess
import os
from modules import utils
import re

RULES_FILE = "/etc/iptables/rules.v4"
RULES_BACKUP = "/etc/iptables/rules.v4.bak"

def valid_log_prefix(prefix):
    return len(prefix) <= 29 and '"' not in prefix and "'" not in prefix

def valid_log_limit(limit):
    return bool(re.match(r'^\d+/(second|minute|hour|day|s|m|h|d)$', limit))

def toggle_log_rule(chain):
    check = subprocess.run(["sudo", "iptables", "-C", chain, "-j", "LOG"], capture_output=True)

    if check.returncode == 0:
        subprocess.run(["sudo", "iptables", "-D", chain, "-j", "LOG"])
        utils.log(f"Logging disabled on {chain}.", "success")
        return
    
    while True:
        try:
            prefix = ask("Log prefix max 29 chars")
        except KeyboardInterrupt:
            return
        if not prefix or valid_log_prefix(prefix):
            break
        utils.log("Invalid prefix (max 29 chars, no quotes).", "error")

    while True:
        try:
            limit = ask("Rate limit e.g. 5/min")
        except KeyboardInterrupt:
            return
        if not limit or valid_log_limit(limit):
            break
        utils.log("Invalid format. Use e.g. 5/min, 10/hour.", "error")

    
    cmd = ["sudo", "iptables", "-A", chain]
    if limit:
        cmd += ["-m","limit","--limit",limit]
    cmd += ["-j", "LOG"]
    if prefix:
        cmd += ["--log-prefix", prefix]
        
    subprocess.run(cmd)
    utils.log(f"Logging enabled on {chain}.", "success")
    


def edit_rules():
    if not utils.is_service_installed("nano"):
        utils.log("Nano is not installed.")
        confirm = utils.choose(["yes", "no"], "Install nano?")
        if confirm != "yes":
            return
        subprocess.run(["sudo", "apt", "install", "nano", "-y"])

        try:
            input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
        except KeyboardInterrupt:
            pass
        

    os.makedirs("/etc/iptables", exist_ok=True)
    
    current = subprocess.run(["sudo", "iptables-save"], capture_output=True, text=True).stdout
    
    # open the rules file
    with open(RULES_FILE, "w") as f:
        f.write(current)

    # open backup rules file
    with open(RULES_BACKUP, "w") as f:
        f.write(current)

    subprocess.run(["sudo", "nano", RULES_FILE])

    apply = utils.choose(["yes","no"], "Apply changes from file?")
    if apply == "yes":
        
        result = subprocess.run(["sudo", "iptables-restore", RULES_FILE], capture_output=True, text=True)
        
        if result.returncode == 0:
            utils.log("Rules applied.", "success")
        else:
            utils.log(f"Failed to apply rules: {result.stderr.strip()}", "error")
            restore = utils.choose(["yes","no"], f"Restore backup from {RULES_BACKUP}?", "error")
            if restore != "yes":
                return
            subprocess.run(["sudo", "iptables-restore", RULES_BACKUP])
            utils.log("Backup restored.", "success")
        
        try:
            input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
        except KeyboardInterrupt:
            pass

def save_rules():
    confirm = utils.choose(["yes", "no"], "Save current iptables rules?")
    if confirm != "yes":
        return
    
    if not utils.is_service_installed("iptables-save"):
        utils.log("iptables-save not found.", "error")
        return

    os.makedirs("/etc/iptables", exist_ok=True)
    result = subprocess.run(["sudo", "iptables-save"], capture_output=True, text=True)
    with open(RULES_FILE, "w") as f:
        f.write(result.stdout)
    utils.log(f"Rules saved to {RULES_FILE}.", "success")

    if not utils.is_service_installed("iptables-restore"):
        install = utils.choose(["yes", "no"], "iptables-persistent not found. Install it?")
        if install == "yes":
            subprocess.run(["sudo", "apt-get", "install", "-y", "iptables-persistent"])
    
    if utils.is_service_installed("iptables-restore"):
        subprocess.run(["sudo", "netfilter-persistent", "save"])
        utils.log("Rules will persist across reboots.", "success")
    
    try:
        input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
    except KeyboardInterrupt:
        pass


def discard_changes():
    confirm = utils.choose(["yes","no"], f"Discrad changes and restore  from {RULES_FILE}?", "error")
    if confirm != "yes":
        return
    if not os.path.exists(RULES_FILE):
        utils.log(f"No saved rules found at {RULES_FILE}.", "error")

        return
    subprocess.run(["sudo","iptables-restore", RULES_FILE])
    utils.log("Rules restored.", "success")

    try:
        input(f"\n{utils.GRAY}Press Enter to continue...{utils.RESET}")
    except KeyboardInterrupt:
        pass

def ensure_ip_forward():
    with open("/proc/sys/net/ipv4/ip_forward") as f:
        enabled = f.read().strip() == "1"
    if enabled:
        return
    
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"])
    utils.log("ip_forward enabled.", "success")

    persist = utils.choose(["yes", "no"], "Make ip_forward persistent across reboots?")
    if persist == "yes":
        with open("/etc/systctl.d/99-libux.conf", "w") as f:
            f.write("net.ipv4.ip_forward = 1\n")
        utils.log("Saved to /etc/systctl.d/99-libux.conf", "success")

def toggle_policy(chain):
    result = subprocess.run(["sudo", "iptables", "-L", chain, "--line-numbers", "-n"],capture_output=True, text=True)
    current = "DROP" if "policy DROP" in result.stdout else "ACCEPT"
    new_policy = "DROP" if current == "ACCEPT" else "ACCEPT"
    subprocess.run(["sudo", "iptables", "-P", chain, new_policy])
    utils.log(f"{chain} policy: {current} -> {new_policy}", "success")

    if new_policy == "DROP":
        enable_log = utils.choose(["yes","no"], "Enable logging for dropped traffic?")
        if enable_log == "yes":
            toggle_log_rule(chain)

def flush_chain(chain, table="filter"):
    confirm = utils.choose(["yes", "no"], f"WARNING: this will flush all rules in {chain}!", "error")
    if confirm != "yes": 
        return
    cmd = ["sudo","iptables","-F", chain]
    if table != "filter":
        cmd += ["-t", table]
    subprocess.run(cmd)
    utils.log(f"{chain} flushed.", "success")


def rule_exists(cmd):
    check_cmd = [c if c != "-A" else "-C" for c in cmd]
    result = subprocess.run(check_cmd, capture_output=True)
    return result.returncode == 0

def ask(prompt):
    try:
        return input(f"{utils.WHITE}{prompt}{utils.GRAY} (Enter to skip): {utils.RESET}").strip()
    except KeyboardInterrupt:
        return None
    
def ask_required(prompt):
    while True:
        try:
            value = input(f"{utils.WHITE}{prompt}: {utils.RESET}").strip()
            if not value:
                utils.log("This field is required.", "error")
                continue
            return value
        except KeyboardInterrupt:
            return None


def show_chain(chain, table="filter",clear=True, pause=True):
    cmd = ["sudo", "iptables", "--line-numbers", "-n", "-v", "-L", chain, "-t", table]
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.splitlines()

    if clear:
        os.system('clear')
        utils.print_menu_name(f" {chain} ")

    word_colors = {
        "ACCEPT": utils.GREEN,
        "DROP": utils.RED,
        "REJECT": utils.RED,
        "all": utils.GRAY,
        "tcp": utils.WHITE,
        "udp": utils.WHITE,
        "icmp": utils.WHITE,
        "lo": utils.YELLOW
    }

    if lines:
        words = lines[0].split()
        colored = " ".join(
            f"{utils.GREEN}{w}{utils.RESET}" if w =="ACCEPT" else 
            f"{utils.RED}{w}{utils.RESET}" if w == "DROP" else
            f"{word_colors.get(w, utils.PINK)}{w}{utils.RESET}"
            for w in words
        )
        print(colored)
        print()
    
    rows = [l.split() for l in lines[1:] if l.strip()]
    if rows:
        col_count = max(len(r) for r in rows)
        col_widths = [0] * col_count
        for row in rows:
            for i, cell in enumerate(row):
                if i < col_count:
                    col_widths[i] = max(col_widths[i], len(cell))
        for row in rows:
            parts = []
            for i, cell in enumerate(row):
                color = word_colors.get(cell,"")
                reset = utils.RESET if color else ""
                pad = col_widths[i] - len(cell) if i < len(col_widths) - 1 else 0
                parts.append(f"{color}{cell}{reset}{' ' * pad}")
            print("  ".join(parts))
    
    print()

    if pause:
        try:
            input("\nPress Enter to continue...")
        except KeyboardInterrupt:
            pass

def remove_rule(chain, table="filter"):
    while True:
        cmd = ["sudo", "iptables", "--line-numbers", "-n", "-v", "-L", chain]
        if table != "filter":
            cmd += ["-t", table]
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.splitlines()
        rules = []
        for l in lines[2:]:
            parts = l.split()
            if not parts:
                continue
            num    = parts[0]
            target = parts[3] if len(parts) > 3 else "?"
            proto  = parts[4] if len(parts) > 4 else "?"
            iface  = parts[6] if len(parts) > 6 else "?"
            src    = parts[7] if len(parts) > 7 else "?"
            dst    = parts[8] if len(parts) > 8 else "?"
            extra  = " ".join(parts[9:]) if len(parts) > 9 else ""
            rules.append((num, f"{num:<4} {target:<8} {proto:<6} {iface:<8} {src:<20} {dst:<20} {extra}"))

        if not rules:
            utils.log("No rules to remove.", "info")
            return

        os.system('clear')
        utils.print_menu_name(f"Firewall > {chain} > Remove rule")
        print(f"{utils.GRAY}{'#':<4} {'TARGET':<8} {'PROTO':<6} {'IN':<8} {'SRC':<20} {'DST':<20} {'EXTRA'}{utils.RESET}")
        menu = TerminalMenu([r[1] for r in rules], cycle_cursor=True, clear_screen=False, menu_cursor_style=utils.MENU_CURSOR_STYLE)
        choice = utils.show_menu(menu)

        if choice is None:
            return

        line_num = rules[choice][0]
        utils.log(rules[choice][1], "info")
        confirm = utils.choose(["yes", "no"], f"Remove rule {line_num} from {chain}?", "error")
        if confirm != "yes":
            continue
        cmd = ["sudo", "iptables", "-t", table, "-D", chain, line_num] if table != "filter" else ["sudo", "iptables", "-D", chain, line_num]
        subprocess.run(cmd)
        utils.log(f"Rule {line_num} removed from {chain}.", "success")
