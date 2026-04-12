import subprocess


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
