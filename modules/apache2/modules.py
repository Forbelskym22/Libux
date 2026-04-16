import os
import subprocess
from modules import utils
from .shared import MODS_AVAILABLE, MODS_ENABLED

def list_mods(directory):
    try:
        result = subprocess.run(["sudo", "ls", directory], capture_output=True, text=True)
        return sorted(set(
            f.replace(".load", "").replace(".conf", "")
            for f in result.stdout.strip().splitlines()
            if f.endswith(".load")
        ))
    except Exception:
        return []

def show_modules(pause=True):
    os.system("clear")
    utils.print_menu_name("Apache2 Modules")

    available = list_mods(MODS_AVAILABLE)
    enabled = list_mods(MODS_ENABLED)

    for mod in available:
        status = f"{utils.GREEN}[enabled]{utils.RESET}" if mod in enabled else f"{utils.GRAY}[disabled]{utils.RESET}"
        print(f"  {utils.YELLOW}{mod:<32}{utils.RESET} {status}")

    if pause:
        utils.pause()

def enable_module():
    os.system("clear")
    utils.print_menu_name("Enable Module")

    available = list_mods(MODS_AVAILABLE)
    enabled = list_mods(MODS_ENABLED)
    disabled = [m for m in available if m not in enabled]

    if not disabled:
        utils.log("All modules are already enabled.", "info")
        utils.pause()
        return

    mod = utils.choose(disabled, "Select module to enable")
    if mod is None:
        return

    result = subprocess.run(["sudo", "a2enmod", mod], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log(f"{mod} enabled. Restart Apache2 to apply.", "success")
    else:
        utils.log(result.stderr.strip() or "Failed to enable module.", "error")
    utils.pause()

def disable_module():
    os.system("clear")
    utils.print_menu_name("Disable Module")

    enabled = list_mods(MODS_ENABLED)
    if not enabled:
        utils.log("No enabled modules.", "info")
        utils.pause()
        return

    mod = utils.choose(enabled, "Select module to disable")
    if mod is None:
        return

    result = subprocess.run(["sudo", "a2dismod", mod], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log(f"{mod} disabled. Restart Apache2 to apply.", "success")
    else:
        utils.log(result.stderr.strip() or "Failed to disable module.", "error")
    utils.pause()

def manage_modules():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Apache2 Modules")

        options = [
            "Show",     # 0
            "Enable",   # 1
            "Disable",  # 2
            "",         # 3
            "Back",     # 4
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_modules()
        elif choice == 1:
            enable_module()
        elif choice == 2:
            disable_module()
        elif choice == 4 or choice is None:
            return

        last = choice
