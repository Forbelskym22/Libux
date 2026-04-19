import os
import subprocess
from modules import utils

# ── Helpers ────────────────────────────────────────────────────────────────────

def get_local_users():
    """Returns list of (username, uid, gid, home, shell) for non-system users."""
    users = []
    result = subprocess.run(["sudo", "cat", "/etc/passwd"], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        parts = line.split(":")
        if len(parts) < 7:
            continue
        uid = int(parts[2])
        if uid >= 1000 and parts[0] != "nobody":
            users.append({
                "name":  parts[0],
                "uid":   uid,
                "gid":   int(parts[3]),
                "home":  parts[5],
                "shell": parts[6],
            })
    return users

def get_all_groups():
    result = subprocess.run(["sudo", "cat", "/etc/group"], capture_output=True, text=True)
    groups = []
    for line in result.stdout.splitlines():
        parts = line.split(":")
        if len(parts) >= 4:
            groups.append({"name": parts[0], "gid": parts[2], "members": parts[3].split(",") if parts[3] else []})
    return groups

def is_locked(username):
    result = subprocess.run(["sudo", "passwd", "-S", username], capture_output=True, text=True)
    parts = result.stdout.split()
    return len(parts) >= 2 and parts[1] in ("L", "LK")

# ── List ───────────────────────────────────────────────────────────────────────

def show_users():
    os.system("clear")
    utils.print_menu_name("Users")
    users = get_local_users()
    if not users:
        utils.log("No local users found.", "info")
        utils.pause()
        return
    print(f"  {utils.GRAY}{'Username':<20}{'UID':<8}{'Home':<25}{'Shell'}{utils.RESET}")
    print(f"  {utils.GRAY}{'─' * 60}{utils.RESET}")
    for u in users:
        locked = " [locked]" if is_locked(u["name"]) else ""
        name = f"{utils.YELLOW}{u['name']}{utils.GRAY}{locked}{utils.RESET}"
        print(f"  {name:<38}{u['uid']:<8}{utils.WHITE}{u['home']:<25}{utils.GRAY}{u['shell']}{utils.RESET}")
    print()
    utils.pause()

# ── Add user ───────────────────────────────────────────────────────────────────

def add_user():
    os.system("clear")
    utils.print_menu_name("Add user")

    username = utils.ask_required("Username")
    if username is None:
        return

    existing = [u["name"] for u in get_local_users()]
    if username in existing:
        utils.log(f"User '{username}' already exists.", "error")
        utils.pause()
        return

    create_home = utils.choose(["yes", "no"], "Create home directory?") == "yes"
    cmd = ["sudo", "useradd", "-m" if create_home else "-M", username]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to create user.", "error")
        utils.pause()
        return
    utils.log(f"User '{username}' created.", "success")

    if utils.choose(["yes", "no"], "Set password now?") == "yes":
        subprocess.run(["sudo", "passwd", username])

    utils.pause()

# ── Remove user ────────────────────────────────────────────────────────────────

def remove_user():
    os.system("clear")
    utils.print_menu_name("Remove user")

    users = get_local_users()
    if not users:
        utils.log("No local users found.", "info")
        utils.pause()
        return

    names = [u["name"] for u in users]
    username = utils.choose(names, "Select user to remove")
    if username is None:
        return

    if utils.choose(["yes", "no"], f"Remove user '{username}'?", "error") != "yes":
        return

    remove_home = utils.choose(["yes", "no"], "Also delete home directory?") == "yes"
    cmd = ["sudo", "userdel"] + (["-r"] if remove_home else []) + [username]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to remove user.", "error")
    else:
        utils.log(f"User '{username}' removed.", "success")
    utils.pause()

# ── Change password ────────────────────────────────────────────────────────────

def change_password():
    os.system("clear")
    utils.print_menu_name("Change password")

    users = get_local_users()
    if not users:
        utils.log("No local users found.", "info")
        utils.pause()
        return

    names = [u["name"] for u in users]
    username = utils.choose(names, "Select user")
    if username is None:
        return

    subprocess.run(["sudo", "passwd", username])
    utils.pause()

# ── Lock / unlock ──────────────────────────────────────────────────────────────

def toggle_lock():
    os.system("clear")
    utils.print_menu_name("Lock / unlock user")

    users = get_local_users()
    if not users:
        utils.log("No local users found.", "info")
        utils.pause()
        return

    names = [u["name"] for u in users]
    username = utils.choose(names, "Select user")
    if username is None:
        return

    locked = is_locked(username)
    if locked:
        result = subprocess.run(["sudo", "passwd", "-u", username], capture_output=True, text=True)
        utils.log(f"User '{username}' unlocked.", "success" if result.returncode == 0 else "error")
    else:
        result = subprocess.run(["sudo", "passwd", "-l", username], capture_output=True, text=True)
        utils.log(f"User '{username}' locked.", "success" if result.returncode == 0 else "error")
    utils.pause()
