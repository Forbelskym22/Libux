import os
import subprocess
from modules import utils
from .shared import PHPMYADMIN_PACKAGE


def is_installed():
    return utils.is_pkg_installed(PHPMYADMIN_PACKAGE)


def _apache_installed():
    return utils.is_pkg_installed("apache2")


def install_phpmyadmin():
    os.system("clear")
    utils.print_menu_name("Install phpMyAdmin")

    if not _apache_installed():
        utils.log("Apache2 is not installed.", "error")
        utils.log("Install it first via the Apache2 module, then come back here.", "info")
        utils.pause()
        return

    print(f"\n  {utils.WHITE}The installer will ask a few questions:{utils.RESET}")
    print(f"  {utils.GRAY}  1) Web server to configure → select {utils.YELLOW}apache2{utils.GRAY} with Space, then Enter{utils.RESET}")
    print(f"  {utils.GRAY}  2) Configure database with dbconfig-common → {utils.YELLOW}Yes{utils.RESET}")
    print(f"  {utils.GRAY}  3) Application password → choose one (used only internally by phpMyAdmin){utils.RESET}")
    print()
    if utils.choose(["Continue", "Cancel"]) != "Continue":
        return

    subprocess.run(["sudo", "apt", "update"])
    subprocess.run(["sudo", "apt", "install", PHPMYADMIN_PACKAGE, "-y"])

    if is_installed():
        utils.log("phpMyAdmin installed.", "success")
        utils.log("Access it at: http://<server-ip>/phpmyadmin", "info")
    else:
        utils.log("Installation failed or was cancelled.", "error")

    utils.pause()
