from simple_term_menu import TerminalMenu
import subprocess
import os
from modules import utils


def ask(prompt):
    try:
        return input(f"{utils.WHITE}{prompt}{utils.GRAY} (Enter to skip): {utils.RESET}").strip()
    except KeyboardInterrupt:
        return None


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
