import os
import re
import subprocess
from modules import utils
from .shared import SSHD_CONFIG

# Usernames — POSIX portable: alnum + _ . -, not starting with -, <= 32 chars.
_USER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,31}$")


def _valid_user(user):
    return bool(user) and bool(_USER_RE.match(user))


def get_auth_keys_path(user):
    if user == "root":
        return "/root/.ssh/authorized_keys"
    return f"/home/{user}/.ssh/authorized_keys"

def get_system_users():
    result = subprocess.run(["getent","passwd"],capture_output=True, text=True)
    users = []
    for line in result.stdout.splitlines():
        parts = line.split(":")
        if len(parts) >= 7 and parts[6] in ("/bin/bash", "/bin/sh", "/usr/bin/bash", "/usr/bin/zsh"):
            users.append(parts[0])
    return users

def list_keys(user, pause=False):
    path = get_auth_keys_path(user)
    keys = []
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    keys.append(line)
    except FileNotFoundError:
        pass
    return keys

def show_keys(user, pause=True):
    os.system("clear")
    utils.print_menu_name(f"Authorized keys - {user}")

    keys = list_keys(user)
    if not keys:
        utils.log("No authorized keys.", "info")
    else:
        for i, key in enumerate(keys):
            parts = key.split()
            key_type = parts[0] if len(parts) >= 1 else ""
            comment = parts[2] if len(parts) >= 3 else ""
            print(f"  {utils.PURPLE}{i+1}.{utils.RESET} {utils.YELLOW}{key_type}{utils.RESET} {utils.WHITE}{comment}{utils.RESET}")
            print(f"     {utils.GRAY}{key}{utils.RESET}")
            print()

    if pause:
        utils.pause()


def _write_authorized_keys(user, content):
    """Write `content` to ~user/.ssh/authorized_keys safely:
    - No shell interpolation of file contents.
    - Owned by target user so sshd's StrictModes accepts it.
    Returns (ok, stderr)."""
    if not _valid_user(user):
        return False, f"invalid username: {user!r}"
    path = get_auth_keys_path(user)
    ssh_dir = path.rsplit("/", 1)[0]
    # A tiny shell only for the mkdir+chmod+tee pipeline. File contents go via
    # stdin, never via the argv string, so they can't break the shell.
    script = (
        f'mkdir -p "{ssh_dir}" && chmod 700 "{ssh_dir}" && '
        f'cat > "{path}" && chmod 600 "{path}"'
    )
    result = subprocess.run(
        ["sudo", "-u", user, "bash", "-c", script],
        input=content, text=True, capture_output=True,
    )
    return result.returncode == 0, result.stderr.strip()


def _append_authorized_key(user, key):
    """Append a single public key, reusing the safe writer."""
    current = list_keys(user)
    if key in current:
        return False, "Key already exists."
    new_content = "".join(f"{k}\n" for k in current) + f"{key}\n"
    return _write_authorized_keys(user, new_content)


def add_key(user):
    os.system("clear")
    utils.print_menu_name(f"Add authorized key - {user}")
    show_keys(user, pause=False)

    key = utils.ask_required("Paste public key")
    if key is None:
        return
    key = key.strip()
    if not key or key.startswith("#"):
        utils.log("Empty or invalid key.", "error")
        utils.pause()
        return

    ok, err = _append_authorized_key(user, key)
    if ok:
        utils.log("Key added.", "success")
    else:
        utils.log(err or "Failed to add key.", "error")
    utils.pause()


def remove_key(user):
    os.system("clear")
    utils.print_menu_name(f"Remove authorized key - {user}")

    keys = list_keys(user)
    if not keys:
        utils.log("No authorized keys to remove.", "info")
        utils.pause()
        return

    # Label-with-index so duplicate labels can't collide.
    options = []
    for i, key in enumerate(keys):
        parts = key.split()
        label = f"{parts[0]} {parts[2]}" if len(parts) >= 3 else key[:60]
        options.append(f"{i+1}. {label}")

    choice_idx = utils.show_menu(utils.create_menu(options))
    if choice_idx is None:
        return
    key_to_remove = keys[choice_idx]

    confirm = utils.choose(["yes", "no"], f"Remove this key: {key_to_remove}?", "error")
    if confirm != "yes":
        return

    new_keys = [k for i, k in enumerate(keys) if i != choice_idx]
    new_content = "".join(f"{k}\n" for k in new_keys)
    ok, err = _write_authorized_keys(user, new_content)
    if ok:
        utils.log("Key removed.", "success")
    else:
        utils.log(err or "Failed to remove key.", "error")
    utils.pause()


def generate_key(user):
    os.system("clear")
    utils.print_menu_name(f"Generate SSH key — {user}")

    if not _valid_user(user):
        utils.log(f"Invalid username: {user!r}", "error")
        utils.pause()
        return

    key_type = utils.choose(["ed25519", "rsa", "ecdsa"], "Key type")
    if key_type is None:
        return

    home = "/root" if user == "root" else f"/home/{user}"

    name = utils.ask("Key filename (Enter for default)")
    if name is None:
        return
    filename = name.strip() if name else f"id_{key_type}"
    # Forbid path separators and leading dot-dot to keep the file inside ~/.ssh.
    if "/" in filename or filename in ("", ".", "..") or filename.startswith("-"):
        utils.log("Invalid filename.", "error")
        utils.pause()
        return
    path = f"{home}/.ssh/{filename}"

    utils.log(f"Generating {key_type} key...", "info")
    try:
        # Make sure ~/.ssh exists and is owned by the user.
        subprocess.run(
            ["sudo", "-u", user, "bash", "-c",
             f'mkdir -p "{home}/.ssh" && chmod 700 "{home}/.ssh"'],
            capture_output=True, text=True,
        )
        result = subprocess.run(
            ["sudo", "-u", user, "ssh-keygen", "-t", key_type, "-f", path, "-N", ""],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            utils.log(f"Key generated: {path}", "success")
            pub = subprocess.run(["sudo", "cat", f"{path}.pub"], capture_output=True, text=True)
            print(f"\n  {utils.YELLOW}{pub.stdout.strip()}{utils.RESET}\n")
            print(f"  {utils.WHITE}Copy the PUBLIC key above to the client machine")
            print(f"  and add it to ~/.ssh/authorized_keys, or use ssh-copy-id.")
            print(f"  Private key is at: {utils.YELLOW}{path}{utils.RESET}")
            print(f"  Client connects with: {utils.YELLOW}ssh -i {path} {user}@<server-ip>{utils.RESET}")

            public_key = pub.stdout.strip()
            add_to_auth = utils.choose(["yes", "no"], "Add public key to authorized_keys?")
            if add_to_auth == "yes":
                ok, err = _append_authorized_key(user, public_key)
                if ok:
                    utils.log("Public key added to authorized_keys.", "success")
                else:
                    utils.log(err or "Failed to add to authorized_keys.", "error")
        else:
            utils.log(result.stderr.strip(), "error")
    except KeyboardInterrupt:
        pass
    utils.pause()


def manage_keys():
    users = get_system_users()
    if not users:
        utils.log("No users found.", "error")
        utils.pause()
        return

    user = utils.choose(users, "Select user")
    if user is None:
        return

    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name(f"Keys — {user}")

        options = [
            "Show",         # 0
            "Add",          # 1
            "Remove",       # 2
            "Generate",     # 3
            "",             # 4
            "Back",         # 5
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_keys(user)
        elif choice == 1:
            add_key(user)
        elif choice == 2:
            remove_key(user)
        elif choice == 3:
            generate_key(user)
        elif choice == 5 or choice is None:
            return

        last = choice
