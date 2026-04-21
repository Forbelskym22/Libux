import os
import subprocess
from modules import utils
from .shared import DHCP_SERVICE, DHCP_CONFIG, DHCP_DEFAULTS, DEFAULT_CONFIG


def is_installed():
    return utils.is_pkg_installed("isc-dhcp-server")


def has_subnet():
    try:
        with open(DHCP_CONFIG, "r") as f:
            return "subnet" in f.read()
    except FileNotFoundError:
        return False


def install_dhcp():
    os.system("clear")
    utils.print_menu_name("Install DHCP Server")

    utils.log("Installing isc-dhcp-server...", "info")

    # apt update
    result = subprocess.run(["sudo", "apt", "update"], capture_output=True, text=True)
    if result.returncode != 0:
        utils.log("apt update failed.", "error")
        utils.pause()
        return

    # zakaž autostart - služba bez subnetu spadne
    subprocess.run(
        ["sudo", "bash", "-c",
         "echo 'exit 101' > /usr/sbin/policy-rc.d && chmod +x /usr/sbin/policy-rc.d"],
        capture_output=True, text=True
    )

    result = subprocess.run(
        ["sudo", "apt", "install", "isc-dhcp-server", "-y",
         "-o", "Dpkg::Options::=--force-confnew"]
    )

    # obnov autostart
    subprocess.run(["sudo", "rm", "-f", "/usr/sbin/policy-rc.d"],
                    capture_output=True, text=True)

    if result.returncode != 0:
        utils.log("Installation failed.", "error")
        utils.pause()
        return

    # zapiš výchozí config — interfacy se přidají při přidání subnetu
    try:
        with open(DHCP_CONFIG, "w") as f:
            f.write(DEFAULT_CONFIG)
        with open(DHCP_DEFAULTS, "w") as f:
            f.write('INTERFACESv4=""\n')
            f.write('INTERFACESv6=""\n')
    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        utils.pause()
        return

    if is_installed():
        utils.log("isc-dhcp-server installed.", "success")
        utils.log("Add a subnet to configure an interface and start the service.", "info")
    else:
        utils.log("Installation failed.", "error")

    utils.pause()


def show_status():
    os.system("clear")
    utils.print_menu_name("DHCP Service Status")
    subprocess.run(["sudo", "systemctl", "status", DHCP_SERVICE, "--no-pager"])
    utils.pause()


def start_service():
    if not has_subnet():
        utils.log("No subnet configured. Add a subnet first.", "error")
        utils.pause()
        return
    result = subprocess.run(
        ["sudo", "systemctl", "start", DHCP_SERVICE],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        utils.log("DHCP service started.", "success")
    else:
        utils.log(result.stderr.strip(), "error")
    utils.pause()


def stop_service():
    result = subprocess.run(
        ["sudo", "systemctl", "stop", DHCP_SERVICE],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        utils.log("DHCP service stopped.", "success")
    else:
        utils.log(result.stderr.strip(), "error")
    utils.pause()


def restart_service():
    if not has_subnet():
        utils.log("No subnet configured. Add a subnet first.", "error")
        utils.pause()
        return
    subprocess.run(
        ["sudo", "systemctl", "reset-failed", DHCP_SERVICE],
        capture_output=True, text=True
    )
    result = subprocess.run(
        ["sudo", "systemctl", "restart", DHCP_SERVICE],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        utils.log("DHCP service restarted.", "success")
    else:
        utils.log("Restart failed. Check: systemctl status isc-dhcp-server", "error")
    utils.pause()


def manage_service():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("DHCP Service")

        options = [
            "Status",       # 0
            "Start",        # 1
            "Stop",         # 2
            "Restart",      # 3
            "",             # 4
            "Back",         # 5
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
        elif choice == 5 or choice is None:
            return

        last = choice
