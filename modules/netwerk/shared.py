import subprocess
import ipaddress
from modules import utils

def get_interfaces():
    result = subprocess.run(["ip", "-o", "link", "show"], capture_output=True, text=True)
    interfaces = []
    for line in result.stdout.splitlines():
        parts = line.split()
        name = parts[1].strip(":")
        state = "UP" if "UP" in parts else "DOWN"
        interfaces.append({"name": name, "state": state})
    return interfaces


def get_interface_ips(iface):
    result = subprocess.run(["ip", "-o", "addr", "show", iface], capture_output=True, text=True)
    ips = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if "inet" in parts:
            idx = parts.index("inet")
            ips.append(parts[idx + 1])
    return ips

def ask_interface_ip(prompt="IP/prefix (e.g. 192.168.1.10/24)"):
    while True:
        value = utils.ask_required(prompt)
        if value is None:
            return None
        try:
            ipaddress.ip_interface(value)
            return value
        except ValueError:
            utils.log("Invalid IP/prefix.", "error")

