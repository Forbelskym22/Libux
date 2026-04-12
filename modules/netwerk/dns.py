import os
import subprocess
from modules import utils

RESOLV_CONF = "/etc/resolv.conf"

def get_dns_servers():
    servers = []
    try:
        with open(RESOLV_CONF, "r") as f:
            for line in f:
                if line.startswith("nameserver"):
                    parts = line.split()
                    if len(parts) >= 2:
                        servers.append(parts[1])
    except FileNotFoundError:
        pass
    return servers

def show_dns(pause = True):
    os.system("clear")
    utils.print_menu_name("DNS servers")
    servers = get_dns_servers()
    if not servers:
        utils.log("No DNS servers configured.", "info")
    for s in servers:
        print(f"  {utils.WHITE}nameserver {utils.GREEN}{s}{utils.RESET}")
    if pause:
        utils.pause()

def add_dns():
    os.system("clear")
    utils.print_menu_name("Add DNS server")
    show_dns(pause=False)

    ip=utils.ask_ip("DNS server IP")
    if not ip:
        return
    
    servers = get_dns_servers()
    if ip in servers:
        utils.log("DNS server already exists", "error")
        utils.pause()
        return
    with open(RESOLV_CONF, "a") as f:
        f.write(f"\nnameserver {ip}\n")

    utils.log(f"DNS server {ip} added.", "success")
    utils.pause()

def remove_dns():
    os.system("clear")
    utils.print_menu_name("Remove DNS server")

    servers = get_dns_servers()
    if not servers:
        utils.log("No DNS servers to remove.", "error")
        utils.pause()
        return
    
    choice = utils.choose(servers, "Select DNS server to remove")
    if choice is None:
        return
    
    lines=[]
    with open(RESOLV_CONF, "r") as f:
        for line in f:
            if line.strip() == f"nameserver {choice}":
                continue
            lines.append(line)
        with open(RESOLV_CONF, "w") as f:
            f.writelines(lines)
        
        utils.log(f"DNS server {choice} removed.", "success")
        utils.pause()

def manage_dns():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("DNS")

        options = [
            "Show",     # 0
            "Add",      # 1
            "Remove",   # 2
            "",         # 3
            "Back",     # 4
        ]

        menu = utils.create_menu(options,last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_dns()
        elif choice == 1:
            add_dns()
        elif choice == 2:
            remove_dns()
        elif choice == 4 or choice is None:
            break

        last = choice
