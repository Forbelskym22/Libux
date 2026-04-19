import os
import subprocess
from modules import utils
from modules.users.users import get_local_users
from modules.users.groups import get_user_groups

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

    users  = [u["name"] for u in get_local_users()]
    groups = [g["name"] for g in get_user_groups()]

    user = utils.choose(users + ["(type manually)"], "Select user")
    if user is None:
        return
    if user == "(type manually)":
        user = utils.ask_required("Username")
        if user is None:
            return

    include_group = utils.choose(["yes", "no"], "Also set group?") == "yes"
    if include_group:
        group = utils.choose(groups + ["(type manually)"], "Select group")
        if group is None:
            return
        if group == "(type manually)":
            group = utils.ask_required("Group")
            if group is None:
                return
        owner = f"{user}:{group}"
    else:
        owner = user

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
    groups = [g["name"] for g in get_user_groups()]
    group = utils.choose(groups + ["(type manually)"], "Select group")
    if group is None:
        return
    if group == "(type manually)":
        group = utils.ask_required("Group")
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

PRESETS = [
    ("644", "rw-r--r--", "File: owner can read/write, everyone else can read"),
    ("755", "rwxr-xr-x", "Dir/script: owner full access, everyone can read & enter"),
    ("600", "rw-------", "Private file: only owner can read/write"),
    ("700", "rwx------", "Private dir/script: only owner has any access"),
    ("750", "rwxr-x---", "Dir/script: owner full, group can read & enter, others nothing"),
    ("640", "rw-r-----", "File: owner read/write, group read, others nothing"),
    ("777", "rwxrwxrwx", "Everyone full access (not recommended)"),
    ("(manual)", "",       "Enter octal or symbolic mode manually (e.g. 754, u+x, go-w)"),
]

def change_permissions():
    os.system("clear")
    utils.print_menu_name("Change permissions")
    path = utils.pick_path(start="/")
    if path is None:
        return

    os.system("clear")
    utils.print_menu_name(f"Change permissions - {path}")

    # show current permissions
    result = subprocess.run(["stat", "-c", "%A %a", path], capture_output=True, text=True)
    if result.returncode == 0:
        symbolic, octal = result.stdout.strip().split()
        print(f"  {utils.GRAY}Current: {utils.YELLOW}{symbolic}  ({octal}){utils.RESET}\n")

    # preset menu with descriptions
    labels = [
        f"{octal:<8} {sym:<12} {utils.GRAY}{desc}{utils.RESET}"
        if octal != "(manual)" else f"(manual entry)"
        for octal, sym, desc in PRESETS
    ]
    choice = utils.choose(labels, "Select permission preset")
    if choice is None:
        return

    idx = labels.index(choice)
    octal, _, _ = PRESETS[idx]

    if octal == "(manual)":
        print(f"\n  {utils.GRAY}Octal (e.g. 755) or symbolic (e.g. u+x, go-w){utils.RESET}")
        mode = utils.ask_required("Mode")
        if mode is None:
            return
    else:
        mode = octal

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
