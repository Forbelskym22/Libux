import shutil

#colors
RED = "\033[91m"
GREEN = "\033[92m"
ORANGE = "\033[38;5;208m"
WHITE = "\033[97m"

RESET = "\033[0m"
PREFIX = f"{ORANGE}[Libux]{RESET}"

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


def print_menu_name(title):
    """
    Print menu header with orange highlight 
    """
    print(f"{ORANGE}---{RESET} {WHITE}{title}{RESET} {ORANGE}---{RESET}")

