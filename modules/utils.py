import shutil

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
