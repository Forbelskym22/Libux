import os
import subprocess
from modules import utils

# ── View ───────────────────────────────────────────────────────────────────────

def view_permissions():
    os.system("clear")
    utils.print_menu_name("View permissions")
    path = utils.pick_path(start="/")
    if path is None:
        return
    os.system("clear")
    utils.print_menu_name(f"Permissions - {path}")
    result = subprocess.run(["ls", "-la", path], capture_output=True, text=True)
    print(result.stdout)
    utils.pause()

# ── Change owner ───────────────────────────────────────────────────────────────

def change_owner():
    os.system("clear")
    utils.print_menu_name("Change owner")
    path = utils.pick_path(start="/")
    if path is None:
        return

    os.system("clear")
    utils.print_menu_name(f"Change owner - {path}")
    print(f"  {utils.GRAY}Format: user or user:group{utils.RESET}")
    owner = utils.ask_required("New owner (e.g. www-data or www-data:www-data)")
    if owner is None:
        return

    recursive = utils.choose(["yes", "no"], "Apply recursively?") == "yes"
    cmd = ["sudo", "chown"] + (["-R"] if recursive else []) + [owner, path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to change owner.", "error")
    else:
        utils.log(f"Owner of '{path}' set to {owner}.", "success")
    utils.pause()

# ── Change group ───────────────────────────────────────────────────────────────

def change_group():
    os.system("clear")
    utils.print_menu_name("Change group")
    path = utils.pick_path(start="/")
    if path is None:
        return

    os.system("clear")
    utils.print_menu_name(f"Change group - {path}")
    group = utils.ask_required("New group")
    if group is None:
        return

    recursive = utils.choose(["yes", "no"], "Apply recursively?") == "yes"
    cmd = ["sudo", "chgrp"] + (["-R"] if recursive else []) + [group, path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to change group.", "error")
    else:
        utils.log(f"Group of '{path}' set to {group}.", "success")
    utils.pause()

# ── Change permissions ─────────────────────────────────────────────────────────

def change_permissions():
    os.system("clear")
    utils.print_menu_name("Change permissions")
    path = utils.pick_path(start="/")
    if path is None:
        return

    os.system("clear")
    utils.print_menu_name(f"Change permissions - {path}")
    print(f"  {utils.GRAY}Octal (e.g. 755, 644) or symbolic (e.g. u+x, go-w){utils.RESET}")
    mode = utils.ask_required("Mode")
    if mode is None:
        return

    recursive = utils.choose(["yes", "no"], "Apply recursively?") == "yes"
    cmd = ["sudo", "chmod"] + (["-R"] if recursive else []) + [mode, path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to change permissions.", "error")
    else:
        utils.log(f"Permissions of '{path}' set to {mode}.", "success")
    utils.pause()

# ── Permissions menu ───────────────────────────────────────────────────────────

def permissions_menu():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("File Permissions")
        options = [
            "View permissions",   # 0
            "Change owner",       # 1
            "Change group",       # 2
            "Change permissions", # 3
            "",                   # 4
            "Back",               # 5
        ]
        choice = utils.show_menu(utils.create_menu(options, last))
        if choice == 0:
            view_permissions()
        elif choice == 1:
            change_owner()
        elif choice == 2:
            change_group()
        elif choice == 3:
            change_permissions()
        elif choice == 5 or choice is None:
            return
        last = choice
