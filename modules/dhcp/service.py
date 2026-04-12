import os
import subprocess
from modules import utils
from .shared import DHCP_SERVICE, DHCP_CONFIG

def is_installed():
    return utils.is_binary_installed("dhcpd")

def install_dhcp():
    os.system("clear")
    utils.print_menu_name("Install DHCP Server")

    # vyber interface
    iface = utils.pick_interface("DHCP server interface")
    if iface is None:
        return

    utils.log("Installing isc-dhcp-server...", "info")
    subprocess.run(["sudo", "apt", "update"])

    # zakáž autostart během instalace
    subprocess.run(["sudo", "bash", "-c", "echo 'exit 101' > /usr/sbin/policy-rc.d && chmod +x /usr/sbin/policy-rc.d"])

    subprocess.run([
        "sudo", "apt", "install", "isc-dhcp-server", "-y",
        "-o", "Dpkg::Options::=--force-confnew"
    ])

    # obnov autostart
    subprocess.run(["sudo", "rm", "-f", "/usr/sbin/policy-rc.d"])

    # zapiš config PO instalaci
    try:
        import pathlib
        pathlib.Path("/etc/dhcp").mkdir(parents=True, exist_ok=True)
        with open(DHCP_CONFIG, "w") as f:
            f.write("# Libux DHCP configuration\n")
            f.write("default-lease-time 600;\n")
            f.write("max-lease-time 7200;\n")
        with open("/etc/default/isc-dhcp-server", "w") as f:
            f.write(f'INTERFACESv4="{iface}"\n')
            f.write('INTERFACESv6=""\n')
    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        utils.pause()
        return

    # nastartuj service
    utils.log("Starting DHCP service...", "info")
    result = subprocess.run(["sudo", "systemctl", "start", DHCP_SERVICE], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log("DHCP service started.", "success")
    else:
        utils.log("Service start failed — add a subnet first.", "error")

    if is_installed():
        utils.log(f"isc-dhcp-server installed on {iface}.", "success")
    else:
        utils.log("Installation failed.", "error")

    utils.pause()


def show_status():
    os.system("clear")
    utils.print_menu_name("DHCP Service status")
    subprocess.run(["systemctl", "status", DHCP_SERVICE])
    utils.pause()

def start_service():
    result = subprocess.run(["sudo", "systemctl", "start", DHCP_SERVICE], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log("DHCP service started.", "success")
    else:
        utils.log(result.stderr.strip(), "error")
    utils.pause()

def stop_service():
    result = subprocess.run(["sudo", "systemctl", "stop", DHCP_SERVICE], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log("DHCP service stopped.", "success")
    else:
        utils.log(result.stderr.strip(), "error")
    utils.pause()

def restart_service():
    result = subprocess.run(["sudo", "systemctl", "restart", DHCP_SERVICE], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log("DHCP service restarted.", "success")
    else:
        utils.log(result.stderr.strip(), "error")
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