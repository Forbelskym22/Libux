import os
import subprocess
from modules import utils
from .shared import SSHD_CONFIG

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

def add_key(user):
    os.system("clear")
    utils.print_menu_name(f"Add authorized key - {user}")
    show_keys(user, pause=False)

    key = utils.ask_required("Paste public key")
    if key is None:
        return
    
    path = get_auth_keys_path(user)

    try:
        subprocess.run(["sudo", "mkdir", "-p", str(path).rsplit("/",1)[0]],capture_output=True, text=True)
        subprocess.run(["sudo", "chmod", "700", str(path).rsplit("/",1)[0]],capture_output=True, text=True)
        
        existing = list_keys(user)
        if key in existing:
            utils.log("Key already exists.", "error")
            utils.pause()
            return
        
        result = subprocess.run(
            ["sudo","bash","-c",f"echo '{key}' >> {path} && chmod 600 {path}"],
            capture_output=True, text=True
        )

    except Exception as e:
        utils.log(f"Failed: {e}", "error")
    
    utils.pause()

def remove_key(user):
    os.system("clear")
    utils.print_menu_name(f"Remove authorized key - {user}")

    keys =list_keys(user)

    options = []
    for key in keys:
        parts = key.split()
        label = f"{parts[0]} {parts[2]}" if len(parts) >= 3 else key[:60]
        options.append(label)

    choice = utils.choose(options, "Select key to remove")
    if choice is None:
        return
    

    idx = options.index(choice)
    key_to_remove = keys[idx]

    confirm = utils.choose(["yes","no"], f"Remove this key: {key_to_remove}?", "error")
    if confirm != "yes":
        return
    
    path = get_auth_keys_path(user)
    try:
        with open(path, "r") as f:
            lines = f.readlines()
        new_lines = [l for l in lines if l.strip() != key_to_remove]
        result = subprocess.run(
            ["sudo","bash", "-c", f"cat > {path}"],
            input="".join(new_lines), text=True, capture_output=True
            )
        if result.returncode == 0:
            utils.log("Key removed.", "success")
        else:
            utils.log(result.stderr.strip(), "error")
    except Exception as e:
        utils.log(f"Failed: {e}", "error")
    utils.pause()

def generate_key(user):
    os.system("clear")
    utils.print_menu_name(f"Generate SSH key — {user}")

    key_type = utils.choose(["ed25519", "rsa", "ecdsa"], "Key type")
    if key_type is None:
        return

    home = "/root" if user == "root" else f"/home/{user}"

    name = utils.ask("Key filename (Enter for default)")
    if name is None:
        return
    filename = name if name else f"id_{key_type}"
    path = f"{home}/.ssh/{filename}"

    utils.log(f"Generating {key_type} key...", "info")
    try:
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
                auth_path = get_auth_keys_path(user)
                subprocess.run(
                    ["sudo", "bash", "-c", f"mkdir -p {home}/.ssh && echo '{public_key}' >> {auth_path} && chmod 600 {auth_path}"],
                    capture_output=True, text=True
                )
                utils.log("Public key added to authorized_keys.", "success")


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