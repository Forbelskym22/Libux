import getpass
import os
import subprocess
from modules import utils
from .shared import MARIADB_SERVICE, MARIADB_PACKAGE


def is_installed():
    return utils.is_pkg_installed(MARIADB_PACKAGE) and utils.is_binary_installed("mariadb")


def _service_running():
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", MARIADB_SERVICE],
        capture_output=True
    )
    return result.returncode == 0


def install_mariadb():
    os.system("clear")
    utils.print_menu_name("Install MariaDB")
    utils.log("Installing mariadb-server...", "info")

    result = subprocess.run(["sudo", "apt", "update"], capture_output=True, text=True)
    if result.returncode != 0:
        utils.log("apt update failed", "error")
        utils.pause()
        return

    subprocess.run(["sudo", "apt", "install", MARIADB_PACKAGE, "-y"])

    if not is_installed():
        utils.log("Installation failed.", "error")
        utils.pause()
        return

    utils.log("mariadb-server installed.", "success")
    print()
    if utils.choose(["Yes, set it now", "Skip"], "Set root password now?") == "Yes, set it now":
        set_root_password()
    else:
        utils.log("You can set it later via MariaDB menu -> Set root password.", "info")
        utils.pause()


def show_status():
    os.system("clear")
    utils.print_menu_name("MariaDB Service status")
    subprocess.run(["sudo", "systemctl", "status", MARIADB_SERVICE, "--no-pager"])
    utils.pause()


def _systemctl_action(action, past_tense):
    try:
        result = subprocess.run(
            ["sudo", "systemctl", action, MARIADB_SERVICE],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            utils.log(f"MariaDB service {past_tense}.", "success")
        else:
            utils.log(f"MariaDB service failed to {action}.", "error")
            if result.stderr.strip():
                print(f"\n{utils.GRAY}{result.stderr.strip()}{utils.RESET}\n")
    except KeyboardInterrupt:
        utils.log("Cancelled.", "info")
    utils.pause()


def set_root_password():
    os.system("clear")
    utils.print_menu_name("Set MariaDB root password")

    if not _service_running():
        utils.log("MariaDB service is not running. Start it first via Service menu.", "error")
        utils.pause()
        return

    print(f"\n  {utils.GRAY}Sets a password for root@localhost while keeping unix_socket auth,{utils.RESET}")
    print(f"  {utils.GRAY}so `sudo mariadb` keeps working on this host without a password.{utils.RESET}")
    print(f"  {utils.GRAY}The password is used for remote/tool access (phpMyAdmin, `mariadb -u root -p`).{utils.RESET}\n")

    try:
        pw1 = getpass.getpass(f"  {utils.WHITE}New password: {utils.RESET}")
        pw2 = getpass.getpass(f"  {utils.WHITE}Confirm:      {utils.RESET}")
    except (KeyboardInterrupt, EOFError):
        print()
        return

    if not pw1:
        utils.log("Password cannot be empty.", "error")
        utils.pause()
        return
    if pw1 != pw2:
        utils.log("Passwords do not match.", "error")
        utils.pause()
        return

    # escape backslash first, then single quote
    pw_esc = pw1.replace("\\", "\\\\").replace("'", "\\'")

    # MariaDB 10.4+ supports multi-plugin auth:
    #   ALTER USER ... IDENTIFIED VIA unix_socket OR mysql_native_password ...
    # Older versions (Debian 10 ships 10.3) need the classic SET PASSWORD path.
    sql_modern = (
        "ALTER USER 'root'@'localhost' "
        "IDENTIFIED VIA unix_socket "
        f"OR mysql_native_password USING PASSWORD('{pw_esc}');\n"
        "FLUSH PRIVILEGES;\n"
    )
    sql_legacy = (
        f"SET PASSWORD FOR 'root'@'localhost' = PASSWORD('{pw_esc}');\n"
        "FLUSH PRIVILEGES;\n"
    )

    result = subprocess.run(
        ["sudo", "mariadb"],
        input=sql_modern, text=True, capture_output=True
    )
    if result.returncode == 0:
        utils.log("Root password set (unix_socket auth preserved).", "success")
        utils.pause()
        return

    err = (result.stderr or "").lower()
    # Syntax error on the multi-plugin form → fall back to the legacy path.
    if "syntax" in err or "error 1064" in err or "you have an error" in err:
        utils.log("Older MariaDB detected; using legacy password syntax.", "info")
        result = subprocess.run(
            ["sudo", "mariadb"],
            input=sql_legacy, text=True, capture_output=True
        )
        if result.returncode == 0:
            utils.log("Root password set.", "success")
            utils.log(
                "Note: on this MariaDB version 'sudo mariadb' may now "
                "ask for a password. Use `mariadb -u root -p`.", "info"
            )
            utils.pause()
            return

    utils.log("Failed to set root password.", "error")
    if result.stderr.strip():
        print(f"\n{utils.GRAY}{result.stderr.strip()}{utils.RESET}\n")
    utils.pause()


def start_service():    _systemctl_action("start",   "started")
def stop_service():     _systemctl_action("stop",    "stopped")
def restart_service():  _systemctl_action("restart", "restarted")
def enable_service():   _systemctl_action("enable",  "enabled (starts on boot)")
def disable_service():  _systemctl_action("disable", "disabled (won't start on boot)")


def manage_service():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("MariaDB Service")

        options = [
            "Status",   # 0
            "Start",    # 1
            "Stop",     # 2
            "Restart",  # 3
            "Enable (start on boot)",   # 4
            "Disable (stop on boot)",   # 5
            "",         # 6
            "Back",     # 7
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_status()
        elif choice == 1:
            start_service()
        elif choice == 2:
            stop_service()
        elif choice == 3:
            restart_service()
        elif choice == 4:
            enable_service()
        elif choice == 5:
            disable_service()
        elif choice == 7 or choice is None:
            return

        last = choice
