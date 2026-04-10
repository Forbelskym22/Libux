import shutil
import subprocess
from simple_term_menu import TerminalMenu
import ipaddress
from modules.fw_shared import ask
 
# simple_term_menu cursor style (globally used)
MENU_CURSOR_STYLE = ("fg_purple", "bold")

#colors
RED = "\033[91m"
GREEN = "\033[92m"
PURPLE = "\033[38;5;135m"
WHITE = "\033[97m"

PINK = "\033[38;5;213m"
YELLOW = "\033[38;5;226m"
ORANGE = "\033[38;5;208m"
GRAY = "\033[38;5;240m"
RESET = "\033[0m"
PREFIX = f"{PURPLE}[Libux]{RESET}"

def ask_ip():
    while True:
        src_ip = ask("Choose source ip / subnet")
        if src_ip is None: return
        if not src_ip or check_ip(src_ip): break
        log("Invalid IP/subnet.", "error")

def check_ip(ip):
    try:
        ipaddress.ip_network(ip, strict = False)
        return True
    except ValueError:
        return False

def check_port(port):
    return port.isdigit() and (0 < int(port) < 65536)

def choose(options, message="", type= "info"):
    if not options:
        log("No options to choose from", "error")
        return None
    if message:
        log(message, type)
    menu = TerminalMenu(options, cycle_cursor=True, clear_screen=False, menu_cursor_style=MENU_CURSOR_STYLE)
    choice = show_menu(menu)
    if choice is None:
        return None
    return options[choice]


def pick_interface(text =""):
    cmd = ["ip", "-o", "link", "show"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    interfaces = [line.split()[1].strip(":") for line in result.stdout.splitlines()]
    

    message = "choose interface"
    if text != "":
        message = message + f" ({text})"
    log(message,"info")

    menu = TerminalMenu(interfaces, cycle_cursor=True, clear_screen=False, menu_cursor_style=MENU_CURSOR_STYLE)
    choice = show_menu(menu)
    if choice is None:
        return None
    return interfaces[choice]

def is_service_installed(service_name):
    """
    Function used to check if the service is installed on our device.
    """
    return shutil.which(service_name) is not None

def log(message,msg_type="info"):
    """
    Writes out a message to the Teminal
    msg_types: 'info' (default), 'success' (green), 'error' (red)
    """
    if(msg_type == "success"):
        print(f"{PREFIX} {GREEN}{message}{RESET}")
    elif(msg_type == "error"):
        print(f"{PREFIX} {RED}{message}{RESET}")
    else:
        print(f"{PREFIX} {WHITE}{message}{RESET}")


def show_menu(menu):
    """
    Wrapper around menu.show() that treats Ctrl+C as cancel (returns None).
    """
    try:
        return menu.show()
    except KeyboardInterrupt:
        return None

def print_menu_name(title):
    """
    Print menu header with purple highlight
    """
    print(f"{PURPLE}---{RESET} {WHITE}{title}{RESET} {PURPLE}---{RESET} {GRAY}Ctrl+C (exit){RESET}")
