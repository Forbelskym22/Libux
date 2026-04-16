import os
import re
import subprocess
from modules import utils
from .shared import APACHE_CONF, PORTS_CONF

def get_listening_ports():
    ports = []
    try:
        with open(PORTS_CONF, "r") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                match = re.match(r"^Listen\s+(\S+)$", stripped, re.IGNORECASE)
                if match:
                    ports.append(match.group(1))
    except FileNotFoundError:
        pass
    return ports

def set_listening_ports(ports):
    try:
        with open(PORTS_CONF, "r") as f:
            lines = f.readlines()

        new_lines = [l for l in lines if not re.match(r"^Listen\s+", l.strip(), re.IGNORECASE)]
        for port in ports:
            new_lines.append(f"Listen {port}\n")

        with open(PORTS_CONF, "w") as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        utils.log(f"Failed to write ports config: {e}", "error")
        return False

def get_conf_value(key):
    try:
        with open(APACHE_CONF, "r") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                match = re.match(rf"^{re.escape(key)}\s+(.+)$", stripped, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
    except FileNotFoundError:
        pass
    return None

def set_conf_value(key, value):
    try:
        with open(APACHE_CONF, "r") as f:
            lines = f.readlines()

        found = False
        new_lines = []
        for line in lines:
            if re.match(rf"^#?\s*{re.escape(key)}\s+", line, re.IGNORECASE):
                new_lines.append(f"{key} {value}\n")
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"\n{key} {value}\n")

        with open(APACHE_CONF, "w") as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        return False

def config_test():
    os.system("clear")
    utils.print_menu_name("Config Test")
    result = subprocess.run(["sudo", "apache2ctl", "configtest"], capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        utils.log("Syntax OK.", "success")
    else:
        utils.log("Config error:", "error")
        print(f"\n{utils.GRAY}{output}{utils.RESET}\n")
    utils.pause()

def show_config(pause=True):
    os.system("clear")
    utils.print_menu_name("Apache2 Config")

    ports = get_listening_ports()
    ports_str = ", ".join(ports) if ports else "none"
    print(f"  {utils.WHITE}{'Listen':<24}{utils.YELLOW}{ports_str}{utils.RESET}")

    keys = ["ServerName", "ServerAdmin", "ServerRoot", "Timeout", "KeepAlive"]
    for key in keys:
        value = get_conf_value(key)
        if value:
            color = utils.YELLOW
            if value == "On":
                color = utils.GREEN
            elif value == "Off":
                color = utils.RED
            print(f"  {utils.WHITE}{key:<24}{color}{value}{utils.RESET}")
        else:
            print(f"  {utils.WHITE}{key:<24}{utils.GRAY}not set{utils.RESET}")

    if pause:
        utils.pause()

def manage_ports():
    while True:
        os.system("clear")
        utils.print_menu_name("Listen Ports")

        ports = get_listening_ports()
        if ports:
            for p in ports:
                print(f"  {utils.YELLOW}{p}{utils.RESET}")
        else:
            utils.log("No ports configured.", "info")
        print()

        options = ["Add port", "Remove port", "", "Back"]
        menu = utils.create_menu(options)
        choice = utils.show_menu(menu)

        if choice == 0:
            port = utils.ask_required("Port number")
            if port is None:
                continue
            if not utils.check_port(port):
                utils.log("Invalid port number.", "error")
                utils.pause()
                continue
            if port in ports:
                utils.log(f"Port {port} is already configured.", "error")
            else:
                ports.append(port)
                set_listening_ports(ports)
                utils.log(f"Port {port} added. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 1:
            if not ports:
                utils.log("No ports to remove.", "error")
                utils.pause()
                continue
            port_choice = utils.choose(ports, "Select port to remove")
            if port_choice is None:
                continue
            ports.remove(port_choice)
            set_listening_ports(ports)
            utils.log(f"Port {port_choice} removed. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 3 or choice is None:
            break

def set_server_name():
    os.system("clear")
    utils.print_menu_name("Set ServerName")
    current = get_conf_value("ServerName")
    if current:
        utils.log(f"Current: {current}", "info")

    name = utils.ask_required("ServerName (e.g. example.com)")
    if name is None:
        return
    if set_conf_value("ServerName", name):
        utils.log(f"ServerName set to {name}. Reload Apache2 to apply.", "success")
    utils.pause()

def set_server_admin():
    os.system("clear")
    utils.print_menu_name("Set ServerAdmin")
    current = get_conf_value("ServerAdmin")
    if current:
        utils.log(f"Current: {current}", "info")

    email = utils.ask_required("ServerAdmin email")
    if email is None:
        return
    if set_conf_value("ServerAdmin", email):
        utils.log(f"ServerAdmin set to {email}. Reload Apache2 to apply.", "success")
    utils.pause()

def manage_config():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Apache2 Config")

        options = [
            "Show",         # 0
            "Config test",  # 1
            "Listen ports", # 2
            "ServerName",   # 3
            "ServerAdmin",  # 4
            "",             # 5
            "Back",         # 6
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_config()
        elif choice == 1:
            config_test()
        elif choice == 2:
            manage_ports()
        elif choice == 3:
            set_server_name()
        elif choice == 4:
            set_server_admin()
        elif choice == 6 or choice is None:
            return

        last = choice
