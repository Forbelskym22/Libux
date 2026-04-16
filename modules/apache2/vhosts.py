import os
import subprocess
from modules import utils
from .shared import SITES_AVAILABLE, SITES_ENABLED

def list_sites(directory):
    try:
        result = subprocess.run(["sudo", "ls", directory], capture_output=True, text=True)
        return [f for f in result.stdout.strip().splitlines() if f.endswith(".conf")]
    except Exception:
        return []

def _parse_vhost_conf(site_conf):
    info = {"port": "-", "server_name": "-", "doc_root": "-"}
    result = subprocess.run(["sudo", "cat", f"{SITES_AVAILABLE}/{site_conf}"], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        stripped = line.strip()
        m = __import__("re").match(r"<VirtualHost\s+[^:]+:(\d+)>", stripped, __import__("re").IGNORECASE)
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

def show_vhosts(pause=True):
    os.system("clear")
    utils.print_menu_name("Virtual Hosts")

    available = list_sites(SITES_AVAILABLE)
    enabled = list_sites(SITES_ENABLED)

    if not available:
        utils.log("No sites available.", "info")
        if pause:
            utils.pause()
        return

    for site in available:
        info = _parse_vhost_conf(site)
        status = f"{utils.GREEN}[enabled]{utils.RESET}" if site in enabled else f"{utils.GRAY}[disabled]{utils.RESET}"
        print(f"  {utils.YELLOW}{site}{utils.RESET} {status}")
        print(f"    {utils.WHITE}Port:        {utils.PURPLE}{info['port']}{utils.RESET}")
        print(f"    {utils.WHITE}ServerName:  {utils.YELLOW}{info['server_name']}{utils.RESET}")
        print(f"    {utils.WHITE}DocumentRoot:{utils.GRAY} {info['doc_root']}{utils.RESET}")
        print()

    if pause:
        utils.pause()

def enable_site():
    os.system("clear")
    utils.print_menu_name("Enable Site")

    available = list_sites(SITES_AVAILABLE)
    enabled = list_sites(SITES_ENABLED)
    disabled = [s for s in available if s not in enabled]

    if not disabled:
        utils.log("All sites are already enabled.", "info")
        utils.pause()
        return

    site = utils.choose(disabled, "Select site to enable")
    if site is None:
        return

    result = subprocess.run(["sudo", "a2ensite", site], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log(f"{site} enabled. Reload Apache2 to apply.", "success")
    else:
        utils.log(result.stderr.strip() or "Failed to enable site.", "error")
    utils.pause()

def disable_site():
    os.system("clear")
    utils.print_menu_name("Disable Site")

    enabled = list_sites(SITES_ENABLED)
    if not enabled:
        utils.log("No enabled sites.", "info")
        utils.pause()
        return

    site = utils.choose(enabled, "Select site to disable")
    if site is None:
        return

    result = subprocess.run(["sudo", "a2dissite", site], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log(f"{site} disabled. Reload Apache2 to apply.", "success")
    else:
        utils.log(result.stderr.strip() or "Failed to disable site.", "error")
    utils.pause()

def manage_vhosts():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Virtual Hosts")

        options = [
            "Show",     # 0
            "Enable",   # 1
            "Disable",  # 2
            "",         # 3
            "Back",     # 4
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_vhosts()
        elif choice == 1:
            enable_site()
        elif choice == 2:
            disable_site()
        elif choice == 4 or choice is None:
            return

        last = choice


# --- Page management ---

def _get_docroot(site_name):
    conf_path = f"{SITES_AVAILABLE}/{site_name}"
    try:
        result = subprocess.run(["sudo", "cat", conf_path], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("documentroot"):
                parts = stripped.split()
                if len(parts) >= 2:
                    return parts[1]
    except Exception:
        pass
    return None

def create_page():
    os.system("clear")
    utils.print_menu_name("Create Page")

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
        utils.log(f"Site {name}.conf and index.html created.", "success")
    except Exception as e:
        utils.log(f"Failed: {e}", "error")
        utils.pause()
        return

    utils.log("Opening index.html in nano...", "info")
    subprocess.run(["sudo", "nano", index_path])

def edit_page():
    os.system("clear")
    utils.print_menu_name("Edit Page")

    available = list_sites(SITES_AVAILABLE)
    protected = {"000-default.conf", "default-ssl.conf"}
    editable = [s for s in available if s not in protected]

    if not editable:
        utils.log("No pages to edit.", "info")
        utils.pause()
        return

    site = utils.choose(editable, "Select site")
    if site is None:
        return

    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name(f"Edit - {site}")

        options = [
            "Edit HTML (nano)",     # 0
            "Edit vhost config",    # 1
            "",                     # 2
            "Back",                 # 3
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            doc_root = _get_docroot(site)
            if doc_root:
                subprocess.run(["sudo", "nano", f"{doc_root}/index.html"])
            else:
                utils.log("Could not determine DocumentRoot.", "error")
                utils.pause()
        elif choice == 1:
            subprocess.run(["sudo", "nano", f"{SITES_AVAILABLE}/{site}"])
        elif choice == 3 or choice is None:
            return

        last = choice

def remove_page():
    os.system("clear")
    utils.print_menu_name("Remove Page")

    available = list_sites(SITES_AVAILABLE)
    protected = {"000-default.conf", "default-ssl.conf"}
    removable = [s for s in available if s not in protected]

    if not removable:
        utils.log("No pages to remove.", "info")
        utils.pause()
        return

    site = utils.choose(removable, "Select site to remove")
    if site is None:
        return

    confirm = utils.choose(["yes", "no"], f"Remove {site} and its files?", "error")
    if confirm != "yes":
        return

    enabled = list_sites(SITES_ENABLED)
    if site in enabled:
        subprocess.run(["sudo", "a2dissite", site], capture_output=True, text=True)

    doc_root = _get_docroot(site)

    subprocess.run(["sudo", "rm", f"{SITES_AVAILABLE}/{site}"], capture_output=True)

    if doc_root:
        confirm_files = utils.choose(["yes", "no"], f"Also delete document root {doc_root}?", "error")
        if confirm_files == "yes":
            subprocess.run(["sudo", "rm", "-rf", doc_root], capture_output=True)
            utils.log(f"Document root {doc_root} deleted.", "success")

    utils.log(f"{site} removed. Reload Apache2 to apply.", "success")
    utils.pause()

def manage_pages():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Page")

        options = [
            "Create",   # 0
            "Edit",     # 1
            "Remove",   # 2
            "",         # 3
            "Back",     # 4
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            create_page()
        elif choice == 1:
            edit_page()
        elif choice == 2:
            remove_page()
        elif choice == 4 or choice is None:
            return

        last = choice
