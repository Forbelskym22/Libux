DHCP_CONFIG = "/etc/dhcp/dhcpd.conf"
LEASES_FILE = "/var/lib/dhcp/dhcpd.leases"
DHCP_SERVICE = "isc-dhcp-server"
DEFAULT_CONFIG = """# Libux DHCP configuration
default-lease-time 600;
max-lease-time 7200;
"""
