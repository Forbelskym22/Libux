import os
import re
import subprocess
from modules import utils
from .shared import SSH_SERVICE, SSHD_CONFIG

def get_config_value(key):
    try:
        with open(SSHD_CONFIG, "r") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                match = re.match(rf"^{re.escape(key)}\s+(.+)$", stripped, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
    except FileNotFoundError:
        pass
    return None


def set_config_value(key, value):
    try:
        with open(SSHD_CONFIG, "r") as f:
            lines = f.readlines()

        found = False
        new_lines = []
        for line in lines:
            if re.match(rf"^#?\s*{re.escape(key)}\s+", line, re.IGNORECASE):
                new_lines.append(f"{key} {value}\n")
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"\n{key} {value}\n")

        with open(SSHD_CONFIG, "w") as f:
            f.writelines(new_lines)

        return True
    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        return False


DEFAULTS = {
    "Port": "22",
    "PermitRootLogin": "prohibit-password",
    "PasswordAuthentication": "yes",
    "MaxAuthTries": "6",
    "AllowUsers": "all",
    "DenyUsers": "none",
    "Banner": "none",
}

def show_config(pause=True):
    os.system("clear")
    utils.print_menu_name("SSH Config")

    keys = ["Port", "PermitRootLogin", "PasswordAuthentication", "MaxAuthTries", "AllowUsers", "DenyUsers", "Banner"]

    for key in keys:
        value = get_config_value(key)
        if value:
            color = utils.YELLOW
            if value in ("yes", "prohibit-password"):
                color = utils.GREEN
            elif value == "no":
                color = utils.RED
            print(f"  {utils.WHITE}{key:<24}{color}{value}{utils.RESET}")
        else:
            default = DEFAULTS.get(key, "unknown")
            print(f"  {utils.WHITE}{key:<24}{utils.GRAY}default ({default}){utils.RESET}")

    if pause:
        utils.pause()


def set_port():
    os.system("clear")
    utils.print_menu_name("Set SSH Port")
    current = get_config_value("Port") or "22"
    utils.log(f"Current port: {current}", "info")

    while True:
        port = utils.ask_required("New port")
        if port is None:
            return
        if utils.check_port(port):
            break
        utils.log("Invalid port number.", "error")

    if set_config_value("Port", port):
        utils.log(f"Port set to {port}. Restart SSH to apply.", "success")
    utils.pause()


def set_root_login():
    os.system("clear")
    utils.print_menu_name("Permit root login")
    current = get_config_value("PermitRootLogin")
    utils.log(f"Current policy: {current}", "info")

    while True:
        permitroot = utils.choose(["yes", "no", "prohibit-password"], "New policy")
        if permitroot is None:
            return
        else:
            break
    if set_config_value("PermitRootLogin", permitroot):
        utils.log(f"Permit root login policy set to {permitroot}. Restart SSH to apply.", "success")
    utils.pause()

def set_password_auth():
    os.system("clear")
    utils.print_menu_name("Allow password Auth")
    current = get_config_value("PasswordAuthentication")
    utils.log(f"Current policy: {current}", "info")

    while True:
        auth = utils.choose(["yes", "no"], "New policy")
        if auth is None:
            return
        else:
            break
    if set_config_value("PasswordAuthentication", auth):
        utils.log(f"Password authentication set to {auth}. Restart SSH to apply.", "success")
    utils.pause() 

def set_max_auth_tries():
    pass

def set_allow_users():
    pass

def set_deny_users():
    pass

def set_banner():
    pass

def manage_config():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("SSH Config")

        options = [
            "Show",                     # 0
            "Port",                     # 1
            "Root login",               # 2
            "Password authentication",  # 3
            "MaxAuthTries",             # 4
            "AllowUsers",               # 5
            "DenyUsers",                # 6
            "Banner",                   # 7
            "",                         # 8
            "Back",                     # 9
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_config()
        elif choice == 1:
            set_port()
        elif choice == 2:
            set_root_login()
        elif choice == 3:
            set_password_auth()
        elif choice == 4:
            set_max_auth_tries()
        elif choice == 5:
            set_allow_users()
        elif choice == 6:
            set_deny_users()
        elif choice == 7:
            set_banner()
        elif choice == 9 or choice is None:
            return

        last = choice
