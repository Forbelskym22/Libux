import re
import subprocess
from modules import utils
from .shared import SITES_AVAILABLE, SITES_ENABLED

# ── File / group helpers ───────────────────────────────────────────────────────

def list_available():
    try:
        result = subprocess.run(["sudo", "ls", SITES_AVAILABLE], capture_output=True, text=True)
        return [f for f in result.stdout.strip().splitlines() if f.endswith(".conf")]
    except Exception:
        return []

def list_enabled():
    try:
        result = subprocess.run(["sudo", "ls", SITES_ENABLED], capture_output=True, text=True)
        return [f for f in result.stdout.strip().splitlines() if f.endswith(".conf")]
    except Exception:
        return []

def get_base_name(site_conf):
    name = site_conf.replace(".conf", "")
    if name.endswith("-ssl"):
        return name[:-4]
    if name.endswith("-redirect"):
        return name[:-9]
    return name

def group_sites():
    """Returns {base_name: {http, ssl, redirect}} where values are filenames or None."""
    groups = {}
    for site in list_available():
        base = get_base_name(site)
        if base not in groups:
            groups[base] = {"http": None, "ssl": None, "redirect": None}
        if site.endswith("-ssl.conf"):
            groups[base]["ssl"] = site
        elif site.endswith("-redirect.conf"):
            groups[base]["redirect"] = site
        else:
            groups[base]["http"] = site
    return groups

# ── Conf read / write ──────────────────────────────────────────────────────────

def read_conf(site_conf):
    result = subprocess.run(
        ["sudo", "cat", f"{SITES_AVAILABLE}/{site_conf}"],
        capture_output=True, text=True
    )
    return result.stdout

def write_conf(site_conf, content):
    try:
        subprocess.run(
            ["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{site_conf}"],
            input=content, text=True, capture_output=True
        )
        return True
    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        return False

def parse_conf(site_conf):
    info = {"ip": "*", "port": "-", "server_name": "-", "doc_root": "-"}
    result = subprocess.run(
        ["sudo", "cat", f"{SITES_AVAILABLE}/{site_conf}"],
        capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        stripped = line.strip()
        m = re.match(r"<VirtualHost\s+(.+):(\d+)>", stripped, re.IGNORECASE)
        if m:
            info["ip"] = m.group(1)
            info["port"] = m.group(2)
        if stripped.lower().startswith("servername"):
            parts = stripped.split()
            if len(parts) >= 2:
                info["server_name"] = parts[1]
        if stripped.lower().startswith("documentroot"):
            parts = stripped.split()
            if len(parts) >= 2:
                info["doc_root"] = parts[1]
    return info

def set_vhost_port(content, port):
    return re.sub(
        r"(<VirtualHost\s+[^:]+:)\d+(>)", rf"\g<1>{port}\2",
        content, count=1, flags=re.IGNORECASE
    )

def set_vhost_ip(content, ip):
    return re.sub(
        r"(<VirtualHost\s+)[^:]+(:)", rf"\g<1>{ip}\2",
        content, count=1, flags=re.IGNORECASE
    )

def set_directive(content, key, value):
    new_content, count = re.subn(
        rf"^(\s*){re.escape(key)}\s+.+$",
        rf"\g<1>{key} {value}",
        content, flags=re.IGNORECASE | re.MULTILINE
    )
    if count == 0:
        new_content = new_content.replace(
            "</VirtualHost>", f"    {key} {value}\n</VirtualHost>", 1
        )
    return new_content

def enable_conf(site_conf):
    subprocess.run(["sudo", "a2ensite", site_conf], capture_output=True)

def disable_conf(site_conf):
    subprocess.run(["sudo", "a2dissite", site_conf], capture_output=True)

# ── Interface IP picker ────────────────────────────────────────────────────────

def get_interface_ips():
    result = subprocess.run(["ip", "-o", "addr", "show"], capture_output=True, text=True)
    ips = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[2] == "inet":
            ips.append((parts[3].split("/")[0], parts[1]))
    return ips

def pick_listen_ip():
    ips = get_interface_ips()
    options = ["* (all interfaces)"] + [f"{ip}  ({iface})" for ip, iface in ips]
    utils.log("To add or change IP addresses, use the Netwerk section.", "info")
    choice = utils.choose(options, "Select listen IP")
    if choice is None:
        return None
    return "*" if choice.startswith("*") else choice.split()[0]

# ── Vhost templates ────────────────────────────────────────────────────────────

def http_vhost(name, doc_root):
    return (
        f"<VirtualHost *:80>\n"
        f"    ServerName {name}\n"
        f"    DocumentRoot {doc_root}\n\n"
        f"    <Directory {doc_root}>\n"
        f"        Options Indexes FollowSymLinks\n"
        f"        AllowOverride All\n"
        f"        Require all granted\n"
        f"    </Directory>\n\n"
        f"    ErrorLog ${{APACHE_LOG_DIR}}/{name}_error.log\n"
        f"    CustomLog ${{APACHE_LOG_DIR}}/{name}_access.log combined\n"
        f"</VirtualHost>\n"
    )

def ssl_vhost(name, doc_root, cert_path, key_path):
    return (
        f"<VirtualHost *:443>\n"
        f"    ServerName {name}\n"
        f"    DocumentRoot {doc_root}\n\n"
        f"    SSLEngine on\n"
        f"    SSLCertificateFile {cert_path}\n"
        f"    SSLCertificateKeyFile {key_path}\n\n"
        f"    <Directory {doc_root}>\n"
        f"        Options Indexes FollowSymLinks\n"
        f"        AllowOverride All\n"
        f"        Require all granted\n"
        f"    </Directory>\n\n"
        f"    ErrorLog ${{APACHE_LOG_DIR}}/{name}_error.log\n"
        f"    CustomLog ${{APACHE_LOG_DIR}}/{name}_access.log combined\n"
        f"</VirtualHost>\n"
    )

def redirect_vhost(name):
    return (
        f"<VirtualHost *:80>\n"
        f"    ServerName {name}\n"
        f"    Redirect permanent / https://{name}/\n"
        f"</VirtualHost>\n"
    )

def index_html(name):
    return (
        f"<!DOCTYPE html>\n"
        f"<html lang=\"cs\">\n"
        f"<head>\n    <meta charset=\"UTF-8\">\n    <title>{name}</title>\n</head>\n"
        f"<body>\n    <h1>{name}</h1>\n    <p>Toto je stránka {name}.</p>\n</body>\n"
        f"</html>\n"
    )

# ── Display helpers ────────────────────────────────────────────────────────────

def on(val):
    return f"{utils.GREEN}on {utils.RESET}" if val else f"{utils.GRAY}off{utils.RESET}"

def row(label, value, col=22):
    return f"  {utils.GRAY}{label:<{col}}{utils.RESET}{value}"

def divider():
    print(f"  {utils.GRAY}{'─' * 38}{utils.RESET}")
