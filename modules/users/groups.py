import os
import subprocess
from modules import utils
from .users import get_local_users, get_all_groups

# Groups with GID < 1000 that are still useful for regular users
USEFUL_SYSTEM_GROUPS = {
    "sudo", "adm", "www-data", "audio", "video", "plugdev",
    "netdev", "bluetooth", "docker", "lpadmin", "dialout",
    "cdrom", "floppy", "tape", "staff",
}

def get_user_groups():
    """Returns groups relevant for user management."""
    return [
        g for g in get_all_groups()
        if int(g["gid"]) >= 1000 or g["name"] in USEFUL_SYSTEM_GROUPS
    ]

# ── List groups ────────────────────────────────────────────────────────────────

def show_groups():
    os.system("clear")
    utils.print_menu_name("Groups")
    groups = get_all_groups()
    if not groups:
        utils.log("No groups found.", "info")
        utils.pause()
        return
    print(f"  {utils.GRAY}{'Group':<25}{'GID':<8}{'Members'}{utils.RESET}")
    print(f"  {utils.GRAY}{'─' * 60}{utils.RESET}")
    for g in groups:
        members = ", ".join(g["members"]) if g["members"] else "-"
        print(f"  {utils.YELLOW}{g['name']:<25}{utils.RESET}{utils.GRAY}{g['gid']:<8}{utils.WHITE}{members}{utils.RESET}")
    print()
    utils.pause()

# ── Add group ──────────────────────────────────────────────────────────────────

def add_group():
    os.system("clear")
    utils.print_menu_name("Add group")

    groupname = utils.ask_required("Group name")
    if groupname is None:
        return

    existing = [g["name"] for g in get_all_groups()]
    if groupname in existing:
        utils.log(f"Group '{groupname}' already exists.", "error")
        utils.pause()
        return

    result = subprocess.run(["sudo", "groupadd", groupname], capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to create group.", "error")
    else:
        utils.log(f"Group '{groupname}' created.", "success")
    utils.pause()

# ── Remove group ───────────────────────────────────────────────────────────────

def remove_group():
    os.system("clear")
    utils.print_menu_name("Remove group")

    groups = get_all_groups()
    names = [g["name"] for g in groups]
    groupname = utils.choose(names, "Select group to remove")
    if groupname is None:
        return

    if utils.choose(["yes", "no"], f"Remove group '{groupname}'?", "error") != "yes":
        return

    result = subprocess.run(["sudo", "groupdel", groupname], capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to remove group.", "error")
    else:
        utils.log(f"Group '{groupname}' removed.", "success")
    utils.pause()

# ── Manage group membership ────────────────────────────────────────────────────

def manage_membership():
    os.system("clear")
    utils.print_menu_name("Group membership")

    users = get_local_users()
    if not users:
        utils.log("No local users found.", "info")
        utils.pause()
        return

    names = [u["name"] for u in users]
    username = utils.choose(names, "Select user")
    if username is None:
        return

    while True:
        os.system("clear")
        utils.print_menu_name(f"Groups - {username}")

        result = subprocess.run(["groups", username], capture_output=True, text=True)
        current = result.stdout.strip().split(":")[-1].split() if result.stdout else []
        if current:
            print(f"  {utils.GRAY}Current groups: {utils.YELLOW}{', '.join(current)}{utils.RESET}\n")
        else:
            utils.log("No groups.", "info")

        choice = utils.show_menu(utils.create_menu(["Add to group", "Remove from group", "", "Back"]))

        if choice == 0:
            all_groups = [g["name"] for g in get_user_groups()]
            groupname = utils.choose(all_groups, "Select group")
            if groupname is None:
                continue
            result = subprocess.run(["sudo", "usermod", "-aG", groupname, username],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                utils.log(result.stderr.strip() or "Failed to add to group.", "error")
            else:
                utils.log(f"'{username}' added to '{groupname}'.", "success")
            utils.pause()

        elif choice == 1:
            if not current:
                utils.log("No groups to remove from.", "error")
                utils.pause()
                continue
            groupname = utils.choose(current, "Select group to remove from")
            if groupname is None:
                continue
            result = subprocess.run(["sudo", "gpasswd", "-d", username, groupname],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                utils.log(result.stderr.strip() or "Failed to remove from group.", "error")
            else:
                utils.log(f"'{username}' removed from '{groupname}'.", "success")
            utils.pause()

        elif choice == 3 or choice is None:
            return
