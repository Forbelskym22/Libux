import os
import subprocess
from simple_term_menu import TerminalMenu
from modules import utils
from modules.users.users import get_local_users
from modules.users.groups import get_user_groups

# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_current_owner(path):
    """Return (user, group) or (None, None) on failure."""
    result = subprocess.run(["stat", "-c", "%U %G", path], capture_output=True, text=True)
    if result.returncode != 0:
        return None, None
    parts = result.stdout.strip().split()
    if len(parts) != 2:
        return None, None
    return parts[0], parts[1]

def _get_current_mode(path):
    """Return (symbolic, octal) or (None, None) on failure."""
    result = subprocess.run(["stat", "-c", "%A %a", path], capture_output=True, text=True)
    if result.returncode != 0:
        return None, None
    parts = result.stdout.strip().split()
    if len(parts) != 2:
        return None, None
    return parts[0], parts[1]

def _ask_recursive(path):
    """Ask recursive only when path is a directory; files always return False."""
    if not os.path.isdir(path):
        return False
    return utils.choose(["yes", "no"], "Apply recursively?") == "yes"

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

    cur_user, cur_group = _get_current_owner(path)
    if cur_user:
        print(f"  {utils.GRAY}Current: {utils.YELLOW}{cur_user}:{cur_group}{utils.RESET}\n")

    users  = [u["name"] for u in get_local_users()]
    groups = [g["name"] for g in get_user_groups()]

    user_options = users + ["(type manually)"]
    user_cursor = users.index(cur_user) if cur_user in users else 0
    user = utils.choose(user_options, "Select user", cursor_index=user_cursor)
    if user is None:
        return
    if user == "(type manually)":
        user = utils.ask_required("Username")
        if user is None:
            return

    include_group = utils.choose(["yes", "no"], "Also set group?") == "yes"
    if include_group:
        group_options = groups + ["(type manually)"]
        group_cursor = groups.index(cur_group) if cur_group in groups else 0
        group = utils.choose(group_options, "Select group", cursor_index=group_cursor)
        if group is None:
            return
        if group == "(type manually)":
            group = utils.ask_required("Group")
            if group is None:
                return
        owner = f"{user}:{group}"
    else:
        owner = user

    recursive = _ask_recursive(path)
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

    _, cur_group = _get_current_owner(path)
    if cur_group:
        print(f"  {utils.GRAY}Current group: {utils.YELLOW}{cur_group}{utils.RESET}\n")

    groups = [g["name"] for g in get_user_groups()]
    group_options = groups + ["(type manually)"]
    group_cursor = groups.index(cur_group) if cur_group in groups else 0
    group = utils.choose(group_options, "Select group", cursor_index=group_cursor)
    if group is None:
        return
    if group == "(type manually)":
        group = utils.ask_required("Group")
        if group is None:
            return

    recursive = _ask_recursive(path)
    cmd = ["sudo", "chgrp"] + (["-R"] if recursive else []) + [group, path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to change group.", "error")
    else:
        utils.log(f"Group of '{path}' set to {group}.", "success")
    utils.pause()

# ── Change permissions ─────────────────────────────────────────────────────────

def _bit_matrix(current_octal=None):
    """Multi-select matrix for rwx+special bits. Returns octal string or None on cancel."""
    preselected = []
    if current_octal:
        padded  = current_octal.zfill(4)
        special = int(padded[0])
        owner   = int(padded[1])
        group   = int(padded[2])
        other   = int(padded[3])

        bits = [
            owner   & 4, owner   & 2, owner   & 1,
            group   & 4, group   & 2, group   & 1,
            other   & 4, other   & 2, other   & 1,
            special & 4, special & 2, special & 1,
        ]
        preselected = [i for i, b in enumerate(bits) if b]

    options = [
        "Owner:   read     (view file / list dir)",
        "Owner:   write    (modify file / create in dir)",
        "Owner:   execute  (run file / enter dir)",
        "Group:   read",
        "Group:   write",
        "Group:   execute",
        "Other:   read",
        "Other:   write",
        "Other:   execute",
        "Setuid           (file runs with owner's privileges, e.g. passwd)",
        "Setgid           (new files in dir inherit dir's group)",
        "Sticky           (only file owner can delete, e.g. /tmp)",
    ]

    os.system("clear")
    utils.print_menu_name("Permission matrix")
    print()
    print(f"  {utils.WHITE}Controls:{utils.RESET}")
    print(f"    {utils.YELLOW}↑ / ↓{utils.GRAY}        move between bits{utils.RESET}")
    print(f"    {utils.YELLOW}Space / Tab{utils.GRAY}  toggle bit on/off (checked bits show in brackets){utils.RESET}")
    print(f"    {utils.YELLOW}Enter{utils.GRAY}        confirm selection{utils.RESET}")
    print(f"    {utils.YELLOW}Ctrl+C{utils.GRAY}       cancel{utils.RESET}")
    if current_octal:
        print(f"\n  {utils.GRAY}Current mode: {utils.YELLOW}{current_octal}{utils.GRAY} (already pre-selected below){utils.RESET}")
    print()

    menu = TerminalMenu(
        options,
        multi_select=True,
        show_multi_select_hint=True,
        multi_select_select_on_accept=False,
        multi_select_empty_ok=True,
        preselected_entries=preselected or None,
        cycle_cursor=True,
        clear_screen=False,
        menu_cursor_style=utils.MENU_CURSOR_STYLE,
    )
    try:
        chosen = menu.show()
    except KeyboardInterrupt:
        return None
    if chosen is None:
        return None

    selected = set(chosen)
    def has(idx): return idx in selected

    owner   = (4 if has(0) else 0) + (2 if has(1) else 0) + (1 if has(2) else 0)
    group   = (4 if has(3) else 0) + (2 if has(4) else 0) + (1 if has(5) else 0)
    other   = (4 if has(6) else 0) + (2 if has(7) else 0) + (1 if has(8) else 0)
    special = (4 if has(9) else 0) + (2 if has(10) else 0) + (1 if has(11) else 0)

    sym = ""
    for r_i, w_i, x_i in [(0, 1, 2), (3, 4, 5), (6, 7, 8)]:
        sym += ("r" if has(r_i) else "-")
        sym += ("w" if has(w_i) else "-")
        sym += ("x" if has(x_i) else "-")

    octal = f"{special}{owner}{group}{other}" if special else f"{owner}{group}{other}"

    os.system("clear")
    utils.print_menu_name("Permission matrix - confirm")
    print()
    print(f"  {utils.GRAY}{'Entity':<10}{'Permissions':<14}{'Value'}{utils.RESET}")
    print(f"  {utils.GRAY}{'─' * 32}{utils.RESET}")
    print(f"  {utils.YELLOW}{'Owner':<10}{utils.WHITE}{sym[0:3]:<14}{utils.GRAY}{owner}{utils.RESET}")
    print(f"  {utils.YELLOW}{'Group':<10}{utils.WHITE}{sym[3:6]:<14}{utils.GRAY}{group}{utils.RESET}")
    print(f"  {utils.YELLOW}{'Others':<10}{utils.WHITE}{sym[6:9]:<14}{utils.GRAY}{other}{utils.RESET}")
    if special:
        spec_parts = []
        if has(9):  spec_parts.append("setuid")
        if has(10): spec_parts.append("setgid")
        if has(11): spec_parts.append("sticky")
        print(f"  {utils.YELLOW}{'Special':<10}{utils.PURPLE}{' '.join(spec_parts):<14}{utils.GRAY}{special}{utils.RESET}")
    print(f"\n  {utils.GREEN}Result: {octal}  ({sym}){utils.RESET}\n")

    if utils.choose(["yes", "no"], f"Apply {octal}?") != "yes":
        return None
    return octal

def change_permissions():
    os.system("clear")
    utils.print_menu_name("Change permissions")
    path = utils.pick_path(start="/")
    if path is None:
        return

    os.system("clear")
    utils.print_menu_name(f"Change permissions - {path}")

    symbolic, cur_octal = _get_current_mode(path)
    if cur_octal:
        print(f"  {utils.GRAY}Current: {utils.YELLOW}{symbolic}  ({cur_octal}){utils.RESET}\n")

    mode = _bit_matrix(current_octal=cur_octal)
    if mode is None:
        return

    recursive = _ask_recursive(path)
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
