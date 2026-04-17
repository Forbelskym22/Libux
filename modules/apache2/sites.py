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

def _read_conf(site_conf):
    result = subprocess.run(["sudo", "cat", f"{SITES_AVAILABLE}/{site_conf}"], capture_output=True, text=True)
    return result.stdout

def _write_conf(site_conf, content):
    try:
        subprocess.run(
            ["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{site_conf}"],
            input=content, text=True, capture_output=True
        )
        return True
    except Exception as e:
        utils.log(f"Failed to write config: {e}", "error")
        return False

def _set_vhost_port(content, port):
    return re.sub(r"(<VirtualHost\s+[^:]+:)\d+(>)", rf"\g<1>{port}\2", content, count=1, flags=re.IGNORECASE)

def _set_directive(content, key, value):
    pattern = rf"^(\s*){re.escape(key)}\s+.+$"
    replacement = rf"\g<1>{key} {value}"
    new_content, count = re.subn(pattern, replacement, content, flags=re.IGNORECASE | re.MULTILINE)
    if count == 0:
        new_content = new_content.replace("</VirtualHost>", f"    {key} {value}\n</VirtualHost>", 1)
    return new_content

def edit_site_config(site):
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name(f"Config - {site}")

        info = _parse_conf(site)
        print(f"  {utils.WHITE}{'Port':<16}{utils.PURPLE}{info['port']}{utils.RESET}")
        print(f"  {utils.WHITE}{'ServerName':<16}{utils.YELLOW}{info['server_name']}{utils.RESET}")
        print(f"  {utils.WHITE}{'DocumentRoot':<16}{utils.GRAY}{info['doc_root']}{utils.RESET}")
        print()

        options = [
            "Port",             # 0
            "ServerName",       # 1
            "DocumentRoot",     # 2
            "",                 # 3
            "Advanced (nano)",  # 4
            "",                 # 5
            "Back",             # 6
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            new_port = utils.ask_required("New port")
            if new_port is None:
                continue
            if not utils.check_port(new_port):
                utils.log("Invalid port.", "error")
                utils.pause()
                continue
            content = _read_conf(site)
            _write_conf(site, _set_vhost_port(content, new_port))
            utils.log(f"Port set to {new_port}. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 1:
            new_name = utils.ask_required("New ServerName")
            if new_name is None:
                continue
            content = _read_conf(site)
            _write_conf(site, _set_directive(content, "ServerName", new_name))
            utils.log(f"ServerName set to {new_name}. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 2:
            new_root = utils.ask_required("New DocumentRoot")
            if new_root is None:
                continue
            content = _read_conf(site)
            updated = _set_directive(content, "DocumentRoot", new_root)
            updated = re.sub(r"<Directory\s+\S+>", f"<Directory {new_root}>", updated, count=1)
            _write_conf(site, updated)
            utils.log(f"DocumentRoot set to {new_root}. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 4:
            subprocess.run(["sudo", "nano", f"{SITES_AVAILABLE}/{site}"])

        elif choice == 6 or choice is None:
            return

        last = choice

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

def _generate_self_signed_cert(name):
    cert_path = f"/etc/ssl/certs/{name}.crt"
    key_path = f"/etc/ssl/private/{name}.key"
    utils.log("Generating self-signed certificate...", "info")
    result = subprocess.run([
        "sudo", "openssl", "req", "-x509", "-nodes", "-days", "365",
        "-newkey", "rsa:2048",
        "-keyout", key_path,
        "-out", cert_path,
        "-subj", f"/CN={name}"
    ], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log(f"Certificate: {cert_path}", "success")
        utils.log(f"Key:         {key_path}", "success")
        return cert_path, key_path
    else:
        utils.log(result.stderr.strip() or "Failed to generate certificate.", "error")
        return None, None

def _enable_ssl_module():
    result = subprocess.run(["sudo", "a2enmod", "ssl"], capture_output=True, text=True)
    return result.returncode == 0

def generate_ssl(site):
    os.system("clear")
    utils.print_menu_name(f"SSL - {site}")

    info = _parse_conf(site)
    name = info["server_name"] if info["server_name"] != "-" else site.replace(".conf", "")

    utils.log("Enabling ssl module...", "info")
    if not _enable_ssl_module():
        utils.log("Failed to enable ssl module.", "error")
        utils.pause()
        return

    cert_path, key_path = _generate_self_signed_cert(name)
    if not cert_path:
        utils.pause()
        return

    conf_path = f"{SITES_AVAILABLE}/{site}"
    result = subprocess.run(["sudo", "cat", conf_path], capture_output=True, text=True)
    conf_content = result.stdout

    if "SSLEngine" in conf_content:
        utils.log("SSL is already configured in this vhost.", "info")
        utils.pause()
        return

    ssl_block = (
        f"\n    SSLEngine on\n"
        f"    SSLCertificateFile {cert_path}\n"
        f"    SSLCertificateKeyFile {key_path}\n"
    )

    new_conf = conf_content.replace("</VirtualHost>", ssl_block + "</VirtualHost>")

    if "<VirtualHost" in new_conf:
        import re as _re
        new_conf = _re.sub(r"<VirtualHost\s+[^:]+:\d+>", f"<VirtualHost *:443>", new_conf, count=1)

    subprocess.run(
        ["sudo", "bash", "-c", f"cat > {conf_path}"],
        input=new_conf, text=True, capture_output=True
    )

    utils.log("SSL configured. Restart Apache2 to apply.", "success")
    utils.pause()

def add_site():
    os.system("clear")
    utils.print_menu_name("Add Site")

    name = utils.ask_required("Site name (e.g. example.com)")
    if name is None:
        return

    ssl = utils.choose(["HTTP (port 80)", "HTTPS (port 443, self-signed)"], "Protocol")
    if ssl is None:
        return
    use_ssl = ssl.startswith("HTTPS")
    port = "443" if use_ssl else "80"

    doc_root = utils.ask(f"DocumentRoot (Enter for /var/www/{name})")
    if doc_root is None:
        return
    if not doc_root:
        doc_root = f"/var/www/{name}"

    conf_path = f"{SITES_AVAILABLE}/{name}.conf"
    index_path = f"{doc_root}/index.html"

    cert_path = f"/etc/ssl/certs/{name}.crt"
    key_path = f"/etc/ssl/private/{name}.key"

    if use_ssl:
        utils.log("Enabling ssl module...", "info")
        _enable_ssl_module()
        cert_path, key_path = _generate_self_signed_cert(name)
        if not cert_path:
            utils.pause()
            return

    if use_ssl:
        vhost = (
            f"<VirtualHost *:443>\n"
            f"    ServerName {name}\n"
            f"    DocumentRoot {doc_root}\n"
            f"\n"
            f"    SSLEngine on\n"
            f"    SSLCertificateFile {cert_path}\n"
            f"    SSLCertificateKeyFile {key_path}\n"
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
    else:
        vhost = (
            f"<VirtualHost *:80>\n"
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

def _htpasswd_path(site):
    return f"/etc/apache2/.htpasswd_{site.replace('.conf', '')}"

def _auth_enabled(site):
    content = _read_conf(site)
    return "AuthType Basic" in content

def _enable_auth(site, realm):
    htpasswd = _htpasswd_path(site)
    auth_block = (
        f"\n    <Location />\n"
        f"        AuthType Basic\n"
        f"        AuthName \"{realm}\"\n"
        f"        AuthUserFile {htpasswd}\n"
        f"        Require valid-user\n"
        f"    </Location>\n"
    )
    content = _read_conf(site)
    new_content = content.replace("</VirtualHost>", auth_block + "</VirtualHost>")
    _write_conf(site, new_content)

def _disable_auth(site):
    content = _read_conf(site)
    new_content = re.sub(
        r"\s*<Location\s*/\s*>.*?</Location>",
        "", content, flags=re.DOTALL
    )
    _write_conf(site, new_content)

def manage_auth(site):
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name(f"Auth - {site}")

        enabled = _auth_enabled(site)
        status_str = f"{utils.GREEN}enabled{utils.RESET}" if enabled else f"{utils.GRAY}disabled{utils.RESET}"
        print(f"  {utils.WHITE}Basic Auth: {status_str}\n{utils.RESET}")

        toggle_auth = "Disable auth" if enabled else "Enable auth"

        options = [
            toggle_auth,        # 0
            "Add user",         # 1
            "Remove user",      # 2
            "Show users",       # 3
            "",                 # 4
            "Back",             # 5
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            if enabled:
                confirm = utils.choose(["yes", "no"], "Disable auth and remove htpasswd?", "error")
                if confirm == "yes":
                    _disable_auth(site)
                    subprocess.run(["sudo", "rm", "-f", _htpasswd_path(site)], capture_output=True)
                    utils.log("Auth disabled. Reload Apache2 to apply.", "success")
                    utils.pause()
            else:
                subprocess.run(["sudo", "a2enmod", "auth_basic"], capture_output=True)
                realm = utils.ask("Auth realm (Enter for Restricted Area)")
                if realm is None:
                    continue
                if not realm:
                    realm = "Restricted Area"
                _enable_auth(site, realm)
                utils.log("Auth enabled. Add users and reload Apache2 to apply.", "success")
                utils.pause()

        elif choice == 1:
            username = utils.ask_required("Username")
            if username is None:
                continue
            htpasswd = _htpasswd_path(site)
            flag = "-c" if not os.path.exists(htpasswd) else ""
            cmd = ["sudo", "htpasswd"]
            if flag:
                cmd.append(flag)
            cmd += [htpasswd, username]
            result = subprocess.run(cmd)
            if result.returncode == 0:
                utils.log(f"User {username} added.", "success")
            else:
                utils.log("Failed to add user.", "error")
            utils.pause()

        elif choice == 2:
            htpasswd = _htpasswd_path(site)
            result = subprocess.run(["sudo", "cat", htpasswd], capture_output=True, text=True)
            if result.returncode != 0 or not result.stdout.strip():
                utils.log("No users found.", "info")
                utils.pause()
                continue
            users = [line.split(":")[0] for line in result.stdout.strip().splitlines() if ":" in line]
            user = utils.choose(users, "Select user to remove")
            if user is None:
                continue
            subprocess.run(["sudo", "htpasswd", "-D", htpasswd, user], capture_output=True)
            utils.log(f"User {user} removed.", "success")
            utils.pause()

        elif choice == 3:
            os.system("clear")
            utils.print_menu_name(f"Users - {site}")
            htpasswd = _htpasswd_path(site)
            result = subprocess.run(["sudo", "cat", htpasswd], capture_output=True, text=True)
            if result.returncode != 0 or not result.stdout.strip():
                utils.log("No users found.", "info")
            else:
                for line in result.stdout.strip().splitlines():
                    user = line.split(":")[0]
                    print(f"  {utils.YELLOW}{user}{utils.RESET}")
            utils.pause()

        elif choice == 5 or choice is None:
            return

        last = choice

def site_menu(site):
    enabled = list_enabled()
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name(f"Site - {site}")

        is_enabled = site in list_enabled()
        toggle_label = "Disable" if is_enabled else "Enable"

        options = [
            "Show",           # 0
            "Config",         # 1
            "Edit page",      # 2
            toggle_label,     # 3
            "Generate SSL",   # 4
            "Auth",           # 5
            "Logs",           # 6
            "Remove",         # 7
            "",               # 8
            "Back",           # 9
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_site_details(site)
        elif choice == 1:
            edit_site_config(site)
        elif choice == 2:
            edit_page(site)
        elif choice == 3:
            toggle_site(site)
        elif choice == 4:
            generate_ssl(site)
        elif choice == 5:
            manage_auth(site)
        elif choice == 6:
            show_site_logs(site)
        elif choice == 7:
            remove_site(site)
            return
        elif choice == 9 or choice is None:
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
            marker = "[on] " if site in enabled else "[off]"
            site_options.append(f"{marker} {site}")

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
