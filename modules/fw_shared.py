from simple_term_menu import TerminalMenu
import subprocess
import os
from modules import utils

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
    try:
        value = input(f"{utils.WHITE}{prompt}: {utils.RESET}").strip()
        if not value:
            utils.log("This field is required.", "error")
            return ask_required(prompt)
        return value
    except KeyboardInterrupt:
        return None


def show_chain(chain, table="filter"):
    cmd = ["sudo", "iptables", "--line-numbers", "-n", "-v", "-L", chain, "-t", table]
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.splitlines()
    if len(lines) < 3:
        utils.log("No rules...", "error")
        input("\nPress Enter to continue...")
        return
    
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
    
    
    for  l in lines:
        if not l.strip():
            continue
        colored = " ".join(
            f"{word_colors[w]}{w}{utils.RESET}" 
            if w in word_colors 
            else w for w in l.split(" ")
        )
        print(colored)

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
        cmd = ["sudo", "iptables", "-t", table, "-D", chain, line_num] if table != "filter" else ["sudo", "iptables", "-D", chain, line_num]
        subprocess.run(cmd)
        utils.log(f"Rule {line_num} removed from {chain}.", "success")
