import os
import subprocess
from modules import utils

def show_sessions(pause=True):
    os.system("clear")
    utils.print_menu_name("Active SSH sessions")

    result = subprocess.run(["who"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()

    if not lines:
        utils.log("No active sessions", "info")
    else:
        for line in lines:
            parts = line.split()
            user = parts[0] if len(parts) >= 1 else ""
            tty  = parts[1] if len(parts) >= 2 else ""
            date = parts[2] if len(parts) >= 3 else ""
            time = parts[3] if len(parts) >= 4 else ""
            host = parts[4].strip("()") if len(parts) >= 5 else "local"
            print(f"  {utils.PURPLE}{user}{utils.RESET}  {utils.GRAY}{tty}{utils.RESET}  {utils.WHITE}{date} {time}{utils.RESET}  {utils.YELLOW}{host}{utils.RESET}")

    if pause:
        utils.pause()