import os
import subprocess
from modules import utils
from .shared import SSH_SERVICE

def is_installed():
    return utils.is_pkg_installed("openssh-server") and utils.is_binary_installed("sshd")

def install_ssh():
    os.system("clear")
    utils.print_menu_name("Install SSH Server")
    utils.log("Installing openssh-server...", "info")

    result = subprocess.run(["sudo", "apt", "update"], capture_output=True, text=True)
    if result.returncode != 0:
        utils.log("apt update failed", "error")
        utils.pause()
        return

    result = subprocess.run(
        ["sudo", "apt", "install", "openssh-server", "-y"]
    )

    if not is_installed():
        utils.log("Installation failed.", "error")
        utils.pause()
        return

    utils.log("openssh-server installed.", "success")

    enable = subprocess.run(
        ["sudo", "systemctl", "enable", "--now", SSH_SERVICE],
        capture_output=True, text=True
    )
    if enable.returncode == 0:
        utils.log("SSH service enabled and started.", "success")
    else:
        utils.log("SSH installed but failed to enable/start service.", "error")
        if enable.stderr.strip():
            print(f"\n{utils.GRAY}{enable.stderr.strip()}{utils.RESET}\n")

    utils.pause()

def show_status():
    os.system("clear")
    utils.print_menu_name("SSH Service status")
    subprocess.run(["sudo", "systemctl", "status", SSH_SERVICE, "--no-pager"])
    utils.pause()

def start_service():
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "start", SSH_SERVICE],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            utils.log("SSH service started.", "success")
        else:
            utils.log("SSH service failed to start.", "error")
    except KeyboardInterrupt:
        utils.log("Cancelled.", "info")
    utils.pause()


def stop_service():
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "stop", SSH_SERVICE],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            utils.log("SSH service stopped.", "success")
        else:
            utils.log("SSH service failed to stop.", "error")
    except KeyboardInterrupt:
        utils.log("Cancelled.", "info")
    utils.pause()

def restart_service():
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "restart", SSH_SERVICE],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            utils.log("SSH service restarted.", "success")
        else:
            utils.log("SSH service failed to restart.", "error")
    except KeyboardInterrupt:
        utils.log("Cancelled.", "info")
    utils.pause()

def manage_service():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("SSH Service")

        options = [
            "Status",   # 0
            "Start",    # 1
            "Stop",     # 2
            "Restart",  # 3
            "",         # 4
            "Back",     # 5
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