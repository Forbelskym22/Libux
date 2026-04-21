import os
import re
import shutil
import subprocess
import tempfile
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


def _atomic_write(path, data):
    """Write `data` to `path` atomically (tmp in same dir + os.replace).
    Preserves the original file's mode/owner where possible."""
    dir_ = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=".libux-", dir=dir_)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
        try:
            st = os.stat(path)
            os.chmod(tmp, st.st_mode & 0o7777)
            os.chown(tmp, st.st_uid, st.st_gid)
        except FileNotFoundError:
            pass
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _sshd_valid(path):
    """Run `sshd -t -f <path>` and return (ok, stderr)."""
    result = subprocess.run(
        ["sudo", "sshd", "-t", "-f", path],
        capture_output=True, text=True
    )
    return result.returncode == 0, result.stderr.strip()


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

        return _write_and_validate("".join(new_lines))
    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        return False


def _write_and_validate(new_content):
    """Validate new sshd_config content with `sshd -t` on a tmp file,
    then atomically replace SSHD_CONFIG. Returns True on success."""
    dir_ = os.path.dirname(SSHD_CONFIG) or "."
    fd, tmp = tempfile.mkstemp(prefix=".libux-sshd-", dir=dir_)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(new_content)
        ok, err = _sshd_valid(tmp)
        if not ok:
            utils.log("sshd rejected the new config (not applied).", "error")
            if err:
                print(f"\n{utils.GRAY}{err}{utils.RESET}\n")
            return False
        _atomic_write(SSHD_CONFIG, new_content)
        return True
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


DEFAULTS = {
    "Port": "22",
    "PermitRootLogin": "prohibit-password",
    "PasswordAuthentication": "yes",
    "MaxAuthTries": "6",
    "AllowUsers": "all",
    "DenyUsers": "none",
}


def apply_config():
    result = subprocess.run(
        ["sudo", "systemctl", "restart", SSH_SERVICE],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        utils.log("SSH service restarted (change applied).", "success")
    else:
        utils.log("Failed to restart SSH service.", "error")
        if result.stderr.strip():
            print(f"\n{utils.GRAY}{result.stderr.strip()}{utils.RESET}\n")

def show_config(pause=True):
    os.system("clear")
    utils.print_menu_name("SSH Config")

    keys = ["Port", "PermitRootLogin", "PasswordAuthentication", "MaxAuthTries", "AllowUsers", "DenyUsers"]

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
        utils.log(f"Port set to {port}.", "success")
        apply_config()
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
        utils.log(f"Permit root login policy set to {permitroot}.", "success")
        apply_config()
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
        utils.log(f"Password authentication set to {auth}.", "success")
        apply_config()
    utils.pause()

def set_max_auth_tries():
    os.system("clear")
    utils.print_menu_name("Set max auth tries")
    current = get_config_value("MaxAuthTries") or "6"
    utils.log(f"Current: {current}", "info")

    while True:
        number = utils.ask_required("Maximum number of tries")
        if number is None:
            return
        if number.isdigit() and int(number) > 0:
            break
        utils.log("Invalid number.", "error")

    if set_config_value("MaxAuthTries", number):
        utils.log(f"MaxAuthTries set to {number}.", "success")
        apply_config()
    utils.pause()


def _manage_user_list(key, title):
    while True:
        os.system("clear")
        utils.print_menu_name(title)

        raw = get_config_value(key)
        users = raw.split() if raw else []

        if users:
            for u in users:
                print(f"  {utils.YELLOW}{u}{utils.RESET}")
        else:
            utils.log("No users configured.", "info")
        print()

        options = ["Add user", "Remove user", "", "Back"]
        menu = utils.create_menu(options)
        choice = utils.show_menu(menu)

        if choice == 0:
            user = utils.ask_required("Username")
            if user is None:
                continue
            if user in users:
                utils.log(f"{user} is already in the list.", "error")
            else:
                users.append(user)
                set_config_value(key, " ".join(users))
                utils.log(f"{user} added.", "success")
                apply_config()
            utils.pause()

        elif choice == 1:
            if not users:
                utils.log("No users to remove.", "error")
                utils.pause()
                continue
            user_choice = utils.choose(users, "Select user to remove")
            if user_choice is None:
                continue
            users.remove(user_choice)
            applied = False
            if users:
                applied = set_config_value(key, " ".join(users))
            else:
                # odstraň řádek úplně
                try:
                    with open(SSHD_CONFIG, "r") as f:
                        lines = f.readlines()
                    new_lines = [l for l in lines if not re.match(rf"^{re.escape(key)}\s", l, re.IGNORECASE)]
                    applied = _write_and_validate("".join(new_lines))
                except Exception as e:
                    utils.log(f"Failed to write config: {e}", "error")
            if applied:
                utils.log(f"{user_choice} removed.", "success")
                apply_config()
            utils.pause()


        elif choice == 3 or choice is None:
            break


def set_allow_users():
    _manage_user_list("AllowUsers", "AllowUsers")


def set_deny_users():
    _manage_user_list("DenyUsers", "DenyUsers")


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
            "",                         # 7
            "Back",                     # 8
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
        elif choice == 8 or choice is None:
            return

        last = choice
