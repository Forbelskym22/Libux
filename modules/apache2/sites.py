import os
import re
import subprocess
from modules import utils
from .shared import SITES_AVAILABLE, SITES_ENABLED, LOG_DIR

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

def _parse_conf(site_conf):
    info = {"port": "-", "server_name": "-", "doc_root": "-"}
    result = subprocess.run(["sudo", "cat", f"{SITES_AVAILABLE}/{site_conf}"], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        stripped = line.strip()
        m = re.match(r"<VirtualHost\s+[^:]+:(\d+)>", stripped, re.IGNORECASE)
        if m:
            info["port"] = m.group(1)
        if stripped.lower().startswith("servername"):
            parts = stripped.split()
            if len(parts) >= 2:
                info["server_name"] = parts[1]
        if stripped.lower().startswith("documentroot"):
            parts = stripped.split()
            if len(parts) >= 2:
                info["doc_root"] = parts[1]
    return info

def _show_log(log_path, title):
    os.system("clear")
    utils.print_menu_name(title)
    result = subprocess.run(["sudo", "cat", log_path], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        utils.log("Log is empty or not found.", "info")
    else:
        print(result.stdout)
    utils.pause()

def show_site_details(site):
    os.system("clear")
    utils.print_menu_name(f"Site - {site}")
    info = _parse_conf(site)
    enabled = list_enabled()
    status_str = f"{utils.GREEN}enabled{utils.RESET}" if site in enabled else f"{utils.GRAY}disabled{utils.RESET}"
    print(f"  {utils.WHITE}{'Status':<16}{status_str}")
    print(f"  {utils.WHITE}{'Port':<16}{utils.PURPLE}{info['port']}{utils.RESET}")
    print(f"  {utils.WHITE}{'ServerName':<16}{utils.YELLOW}{info['server_name']}{utils.RESET}")
    print(f"  {utils.WHITE}{'DocumentRoot':<16}{utils.GRAY}{info['doc_root']}{utils.RESET}")
    utils.pause()

def toggle_site(site):
    enabled = list_enabled()
    if site in enabled:
        result = subprocess.run(["sudo", "a2dissite", site], capture_output=True, text=True)
        if result.returncode == 0:
            utils.log(f"{site} disabled. Reload Apache2 to apply.", "success")
        else:
            utils.log(result.stderr.strip() or "Failed.", "error")
    else:
        result = subprocess.run(["sudo", "a2ensite", site], capture_output=True, text=True)
        if result.returncode == 0:
            utils.log(f"{site} enabled. Reload Apache2 to apply.", "success")
        else:
            utils.log(result.stderr.strip() or "Failed.", "error")
    utils.pause()

def edit_conf(site):
    subprocess.run(["sudo", "nano", f"{SITES_AVAILABLE}/{site}"])

def edit_page(site):
    info = _parse_conf(site)
    doc_root = info["doc_root"]
    if doc_root == "-":
        utils.log("Could not determine DocumentRoot.", "error")
        utils.pause()
        return
    subprocess.run(["sudo", "nano", f"{doc_root}/index.html"])

def show_site_logs(site):
    site_name = site.replace(".conf", "")
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name(f"Logs - {site}")

        options = [
            "Access log",   # 0
            "Error log",    # 1
            "",             # 2
            "Back",         # 3
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            _show_log(f"{LOG_DIR}/{site_name}_access.log", f"Access log - {site_name}")
        elif choice == 1:
            _show_log(f"{LOG_DIR}/{site_name}_error.log", f"Error log - {site_name}")
        elif choice == 3 or choice is None:
            return

        last = choice

def remove_site(site):
    os.system("clear")
    utils.print_menu_name(f"Remove - {site}")

    confirm = utils.choose(["yes", "no"], f"Remove {site}?", "error")
    if confirm != "yes":
        return

    enabled = list_enabled()
    if site in enabled:
        subprocess.run(["sudo", "a2dissite", site], capture_output=True, text=True)

    info = _parse_conf(site)
    subprocess.run(["sudo", "rm", f"{SITES_AVAILABLE}/{site}"], capture_output=True)

    if info["doc_root"] != "-":
        confirm_files = utils.choose(["yes", "no"], f"Also delete DocumentRoot {info['doc_root']}?", "error")
        if confirm_files == "yes":
            subprocess.run(["sudo", "rm", "-rf", info["doc_root"]], capture_output=True)
            utils.log(f"DocumentRoot {info['doc_root']} deleted.", "success")

    utils.log(f"{site} removed. Reload Apache2 to apply.", "success")
    utils.pause()

def add_site():
    os.system("clear")
    utils.print_menu_name("Add Site")

    name = utils.ask_required("Site name (e.g. example.com)")
    if name is None:
        return

    port = utils.ask("Port (Enter for 80)")
    if port is None:
        return
    if not port:
        port = "80"
    if not utils.check_port(port):
        utils.log("Invalid port.", "error")
        utils.pause()
        return

    doc_root = utils.ask(f"DocumentRoot (Enter for /var/www/{name})")
    if doc_root is None:
        return
    if not doc_root:
        doc_root = f"/var/www/{name}"

    conf_path = f"{SITES_AVAILABLE}/{name}.conf"
    index_path = f"{doc_root}/index.html"

    vhost = (
        f"<VirtualHost *:{port}>\n"
        f"    ServerName {name}\n"
        f"    DocumentRoot {doc_root}\n"
        f"\n"
        f"    <Directory {doc_root}>\n"
        f"        Options Indexes FollowSymLinks\n"
        f"        AllowOverride All\n"
        f"        Require all granted\n"
        f"    </Directory>\n"
        f"\n"
        f"    ErrorLog ${{APACHE_LOG_DIR}}/{name}_error.log\n"
        f"    CustomLog ${{APACHE_LOG_DIR}}/{name}_access.log combined\n"
        f"</VirtualHost>\n"
    )

    index_html = (
        f"<!DOCTYPE html>\n"
        f"<html lang=\"cs\">\n"
        f"<head>\n"
        f"    <meta charset=\"UTF-8\">\n"
        f"    <title>{name}</title>\n"
        f"</head>\n"
        f"<body>\n"
        f"    <h1>{name}</h1>\n"
        f"    <p>Toto je stránka {name}.</p>\n"
        f"</body>\n"
        f"</html>\n"
    )

    try:
        subprocess.run(["sudo", "mkdir", "-p", doc_root], capture_output=True)
        subprocess.run(["sudo", "bash", "-c", f"cat > {conf_path}"], input=vhost, text=True, capture_output=True)
        subprocess.run(["sudo", "bash", "-c", f"cat > {index_path}"], input=index_html, text=True, capture_output=True)
        utils.log(f"{name}.conf and index.html created.", "success")
    except Exception as e:
        utils.log(f"Failed: {e}", "error")
        utils.pause()
        return

    utils.log("Opening index.html in nano...", "info")
    subprocess.run(["sudo", "nano", index_path])

def site_menu(site):
    enabled = list_enabled()
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name(f"Site - {site}")

        is_enabled = site in list_enabled()
        toggle_label = "Disable" if is_enabled else "Enable"

        options = [
            "Show",         # 0
            "Edit config",  # 1
            "Edit page",    # 2
            toggle_label,   # 3
            "Logs",         # 4
            "Remove",       # 5
            "",             # 6
            "Back",         # 7
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_site_details(site)
        elif choice == 1:
            edit_conf(site)
        elif choice == 2:
            edit_page(site)
        elif choice == 3:
            toggle_site(site)
        elif choice == 4:
            show_site_logs(site)
        elif choice == 5:
            remove_site(site)
            return
        elif choice == 7 or choice is None:
            return

        last = choice

def manage_sites():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Sites")

        available = list_available()
        enabled = list_enabled()

        site_options = []
        for site in available:
            marker = f"{utils.GREEN}*{utils.RESET} " if site in enabled else "  "
            site_options.append(f"{marker}{site}")

        options = site_options + ["", "Add site", "", "Back"]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice is None:
            return

        add_index = len(available) + 1
        back_index = len(available) + 3

        if choice < len(available):
            site_menu(available[choice])
        elif choice == add_index:
            add_site()
        elif choice == back_index:
            return

        last = choice
