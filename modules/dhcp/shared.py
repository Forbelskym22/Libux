import subprocess
from modules import utils

DHCP_CONFIG = "/etc/dhcp/dhcpd.conf"
LEASES_FILE = "/var/lib/dhcp/dhcpd.leases"
DHCP_SERVICE = "isc-dhcp-server"
DHCP_DEFAULTS = "/etc/default/isc-dhcp-server"

DEFAULT_CONFIG = """\
# Libux DHCP configuration
default-lease-time 600;
max-lease-time 7200;
"""


def test_config():
    result = subprocess.run(
        ["sudo", "dhcpd", "-t", "-cf", DHCP_CONFIG],
        capture_output=True, text=True
    )
    return result.returncode == 0, result.stderr.strip()


def restart_dhcp():
    try:
        # otestuj config před restartem
        ok, error = test_config()
        if not ok:
            utils.log("Configuration error:", "error")
            for line in error.splitlines():
                line = line.strip()
                if line:
                    print(f"  {utils.GRAY}{line}{utils.RESET}")
            return False

        subprocess.run(
            ["sudo", "systemctl", "reset-failed", DHCP_SERVICE],
            capture_output=True, text=True
        )
        result = subprocess.run(
            ["sudo", "systemctl", "restart", DHCP_SERVICE],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            utils.log("DHCP service restarted.", "success")
        else:
            utils.log("Service failed to restart.", "error")
            log = subprocess.run(
                ["sudo", "journalctl", "-u", DHCP_SERVICE, "-n", "5", "--no-pager", "-q"],
                capture_output=True, text=True
            )
            if log.stdout.strip():
                for line in log.stdout.strip().splitlines():
                    print(f"  {utils.GRAY}{line}{utils.RESET}")
        return result.returncode == 0
    except KeyboardInterrupt:
        utils.log("Cancelled.", "info")
        return False
