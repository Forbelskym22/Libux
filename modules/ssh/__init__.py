import os
import subprocess
from simple_term_menu import TerminalMenu
from modules import utils
from .service import manage_service, is_installed, install_ssh
from .config import manage_config
from .keys import manage_keys
from .sessions import show_sessions

def show_ssh_menu():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Network Connectivity")

        options = [
            "Service",          # 0
            "Config",           # 1
            "Sessions",         # 2   
            "Authorized keys",  # 3      
            "",                 # 4   
            "Back"              # 5  
        ]#

        menu = utils.create_menu(options,last)
        choice = utils.show_menu(menu)  

        if choice == 0:
            manage_service()
        elif choice == 1:
            manage_config()
        elif choice == 3:
            manage_keys()
        elif choice == 2:
            show_sessions()
        elif choice == 5 or choice is None:
            return
        last = choice

def run():
    if not is_installed():
        os.system("clear")
        utils.print_menu_name("SSH Management")
        utils.log("openssh-server is not installed.", "error")
        confirm = utils.choose(["Install", "Back"])
        if confirm == "Install":
            install_ssh()
        else:
            return

    if is_installed():
        show_ssh_menu()