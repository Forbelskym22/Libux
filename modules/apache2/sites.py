import os
import re
import subprocess
from modules import utils
from .shared import SITES_AVAILABLE, SITES_ENABLED, LOG_DIR

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

def _get_base_name(site_conf):
    name = site_conf.replace(".conf", "")
    if name.endswith("-ssl"):
        return name[:-4]
    if name.endswith("-redirect"):
        return name[:-9]
    return name

def _group_sites():
    """Returns {base_name: {http, ssl, redirect}} where values are conf filenames or None."""
    groups = {}
    for site in list_available():
        base = _get_base_name(site)
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

def _read_conf(site_conf):
    result = subprocess.run(
        ["sudo", "cat", f"{SITES_AVAILABLE}/{site_conf}"],
        capture_output=True, text=True
    )
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

def _parse_conf(site_conf):
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

def _set_vhost_port(content, port):
    return re.sub(
        r"(<VirtualHost\s+[^:]+:)\d+(>)", rf"\g<1>{port}\2",
        content, count=1, flags=re.IGNORECASE
    )

def _set_vhost_ip(content, ip):
    return re.sub(
        r"(<VirtualHost\s+)[^:]+(:)", rf"\g<1>{ip}\2",
        content, count=1, flags=re.IGNORECASE
    )

def _set_directive(content, key, value):
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

# ── Interface IP picker ────────────────────────────────────────────────────────

def _get_interface_ips():
    result = subprocess.run(["ip", "-o", "addr", "show"], capture_output=True, text=True)
    ips = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[2] == "inet":
            ips.append((parts[3].split("/")[0], parts[1]))
    return ips

def _pick_listen_ip():
    ips = _get_interface_ips()
    options = ["* (all interfaces)"] + [f"{ip}  ({iface})" for ip, iface in ips]
    utils.log("To add or change IP addresses, use the Netwerk section.", "info")
    choice = utils.choose(options, "Select listen IP")
    if choice is None:
        return None
    return "*" if choice.startswith("*") else choice.split()[0]

# ── ServerAlias ────────────────────────────────────────────────────────────────

def _get_aliases(site_conf):
    for line in _read_conf(site_conf).splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("serveralias"):
            return stripped.split()[1:]
    return []

def manage_aliases(site_conf):
    while True:
        os.system("clear")
        utils.print_menu_name(f"ServerAlias - {site_conf}")

        aliases = _get_aliases(site_conf)
        if aliases:
            for a in aliases:
                print(f"  {utils.YELLOW}{a}{utils.RESET}")
        else:
            utils.log("No aliases configured.", "info")
        print()

        choice = utils.show_menu(utils.create_menu(["Add alias", "Remove alias", "", "Back"]))

        if choice == 0:
            alias = utils.ask_required("Alias (e.g. www.example.com)")
            if alias is None:
                continue
            if alias in aliases:
                utils.log("Alias already exists.", "error")
                utils.pause()
                continue
            aliases.append(alias)
            content = _read_conf(site_conf)
            if re.search(r"ServerAlias", content, re.IGNORECASE):
                new_content = _set_directive(content, "ServerAlias", " ".join(aliases))
            else:
                new_content = re.sub(
                    r"(ServerName\s+\S+)", rf"\1\n    ServerAlias {alias}",
                    content, count=1, flags=re.IGNORECASE
                )
            _write_conf(site_conf, new_content)
            utils.log(f"Alias {alias} added. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 1:
            if not aliases:
                utils.log("No aliases to remove.", "error")
                utils.pause()
                continue
            alias = utils.choose(aliases, "Select alias to remove")
            if alias is None:
                continue
            aliases.remove(alias)
            content = _read_conf(site_conf)
            new_content = (
                _set_directive(content, "ServerAlias", " ".join(aliases))
                if aliases
                else re.sub(r"\n?\s*ServerAlias\s+.+", "", content, flags=re.IGNORECASE)
            )
            _write_conf(site_conf, new_content)
            utils.log(f"Alias {alias} removed. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 3 or choice is None:
            break

# ── Directory listing ──────────────────────────────────────────────────────────

def _directory_listing_enabled(site_conf):
    m = re.search(r"Options\s+([^\n]+)", _read_conf(site_conf), re.IGNORECASE)
    return bool(m and "Indexes" in m.group(1))

def toggle_directory_listing(site_conf):
    content = _read_conf(site_conf)
    if _directory_listing_enabled(site_conf):
        new_content = re.sub(r"(Options\s+[^\n]*)Indexes\s*", r"\1", content, flags=re.IGNORECASE)
        _write_conf(site_conf, new_content)
        utils.log("Directory listing disabled. Reload Apache2 to apply.", "success")
    else:
        new_content = re.sub(r"(Options\s+)", r"\1Indexes ", content, count=1, flags=re.IGNORECASE)
        _write_conf(site_conf, new_content)
        utils.log("Directory listing enabled. Reload Apache2 to apply.", "success")
    utils.pause()

# ── Auth ───────────────────────────────────────────────────────────────────────

def _htpasswd_path(name):
    return f"/etc/apache2/.htpasswd_{name}"

def _auth_enabled(site_conf):
    return "AuthType Basic" in _read_conf(site_conf)

def _enable_auth(site_conf, realm, htpasswd):
    auth_block = (
        f"\n    <Location />\n"
        f"        AuthType Basic\n"
        f"        AuthName \"{realm}\"\n"
        f"        AuthUserFile {htpasswd}\n"
        f"        Require valid-user\n"
        f"    </Location>\n"
    )
    content = _read_conf(site_conf)
    _write_conf(site_conf, content.replace("</VirtualHost>", auth_block + "</VirtualHost>"))

def _disable_auth(site_conf):
    content = _read_conf(site_conf)
    _write_conf(site_conf, re.sub(
        r"\s*<Location\s*/\s*>.*?</Location>", "", content, flags=re.DOTALL
    ))

def manage_auth(name, site_conf):
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name(f"Auth - {name}")

        enabled = _auth_enabled(site_conf)
        status_str = f"{utils.GREEN}enabled{utils.RESET}" if enabled else f"{utils.GRAY}disabled{utils.RESET}"
        print(f"  {utils.WHITE}Basic Auth: {status_str}\n{utils.RESET}")

        options = [
            "Disable auth" if enabled else "Enable auth",
            "Add user", "Remove user", "Show users", "", "Back"
        ]
        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            if enabled:
                confirm = utils.choose(["yes", "no"], "Disable auth and remove htpasswd?", "error")
                if confirm == "yes":
                    _disable_auth(site_conf)
                    subprocess.run(["sudo", "rm", "-f", _htpasswd_path(name)], capture_output=True)
                    utils.log("Auth disabled. Reload Apache2 to apply.", "success")
                    utils.pause()
            else:
                subprocess.run(["sudo", "a2enmod", "auth_basic"], capture_output=True)
                realm = utils.ask("Message of the day (Enter for Restricted Area)")
                if realm is None:
                    continue
                if not realm:
                    realm = "Restricted Area"
                _enable_auth(site_conf, realm, _htpasswd_path(name))
                utils.log("Auth enabled. Add users and reload Apache2 to apply.", "success")
                utils.pause()

        elif choice == 1:
            username = utils.ask_required("Username")
            if username is None:
                continue
            htpasswd = _htpasswd_path(name)
            check = subprocess.run(["sudo", "test", "-f", htpasswd], capture_output=True)
            cmd = ["sudo", "htpasswd"] + (["-c"] if check.returncode != 0 else []) + [htpasswd, username]
            subprocess.run(cmd)
            utils.pause()

        elif choice == 2:
            htpasswd = _htpasswd_path(name)
            result = subprocess.run(["sudo", "cat", htpasswd], capture_output=True, text=True)
            if result.returncode != 0 or not result.stdout.strip():
                utils.log("No users found.", "info")
                utils.pause()
                continue
            users = [l.split(":")[0] for l in result.stdout.strip().splitlines() if ":" in l]
            user = utils.choose(users, "Select user to remove")
            if user is None:
                continue
            subprocess.run(["sudo", "htpasswd", "-D", htpasswd, user], capture_output=True)
            utils.log(f"User {user} removed.", "success")
            utils.pause()

        elif choice == 3:
            os.system("clear")
            utils.print_menu_name(f"Users - {name}")
            result = subprocess.run(["sudo", "cat", _htpasswd_path(name)], capture_output=True, text=True)
            if result.returncode != 0 or not result.stdout.strip():
                utils.log("No users found.", "info")
            else:
                for line in result.stdout.strip().splitlines():
                    print(f"  {utils.YELLOW}{line.split(':')[0]}{utils.RESET}")
            utils.pause()

        elif choice == 5 or choice is None:
            return

        last = choice

# ── SSL ────────────────────────────────────────────────────────────────────────

def _generate_self_signed_cert(name):
    cert_path = f"/etc/ssl/certs/{name}.crt"
    key_path = f"/etc/ssl/private/{name}.key"
    utils.log("Generating self-signed certificate...", "info")
    result = subprocess.run([
        "sudo", "openssl", "req", "-x509", "-nodes", "-days", "365",
        "-newkey", "rsa:2048", "-keyout", key_path, "-out", cert_path,
        "-subj", f"/CN={name}"
    ], capture_output=True, text=True)
    if result.returncode == 0:
        utils.log(f"Certificate: {cert_path}", "success")
        utils.log(f"Key:         {key_path}", "success")
        return cert_path, key_path
    utils.log(result.stderr.strip() or "Failed to generate certificate.", "error")
    return None, None

def _enable_ssl_module():
    return subprocess.run(["sudo", "a2enmod", "ssl"], capture_output=True).returncode == 0

# ── Vhost templates ────────────────────────────────────────────────────────────

def _http_vhost(name, doc_root):
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

def _ssl_vhost(name, doc_root, cert_path, key_path):
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

def _redirect_vhost(name):
    return (
        f"<VirtualHost *:80>\n"
        f"    ServerName {name}\n"
        f"    Redirect permanent / https://{name}/\n"
        f"</VirtualHost>\n"
    )

def _index_html(name):
    return (
        f"<!DOCTYPE html>\n"
        f"<html lang=\"cs\">\n"
        f"<head>\n    <meta charset=\"UTF-8\">\n    <title>{name}</title>\n</head>\n"
        f"<body>\n    <h1>{name}</h1>\n    <p>Toto je stránka {name}.</p>\n</body>\n"
        f"</html>\n"
    )

# ── Display helpers ────────────────────────────────────────────────────────────

def _on(val):
    return f"{utils.GREEN}on {utils.RESET}" if val else f"{utils.GRAY}off{utils.RESET}"

def _row(label, value, col=22):
    return f"  {utils.GRAY}{label:<{col}}{utils.RESET}{value}"

def _divider():
    print(f"  {utils.GRAY}{'─' * 38}{utils.RESET}")

# ── Show ───────────────────────────────────────────────────────────────────────

def show_site_details(name, group):
    os.system("clear")
    utils.print_menu_name(f"Site - {name}")

    enabled = list_enabled()
    main_conf = group["ssl"] or group["http"]
    info = _parse_conf(main_conf) if main_conf else {}
    aliases = _get_aliases(main_conf) if main_conf else []
    auth = _auth_enabled(main_conf) if main_conf else False
    listing = _directory_listing_enabled(main_conf) if main_conf else False

    def _comp_status(conf):
        if not conf:
            return f"{utils.GRAY}none{utils.RESET}"
        return f"{utils.GREEN}on {utils.RESET}" if conf in enabled else f"{utils.GRAY}off{utils.RESET}"

    name_str = (
        f"{utils.YELLOW}{info.get('server_name')}{utils.RESET}"
        if info.get("server_name") not in (None, "-")
        else f"{utils.GRAY}not set{utils.RESET}"
    )
    alias_str = f"{utils.GRAY}{', '.join(aliases)}{utils.RESET}" if aliases else f"{utils.GRAY}none{utils.RESET}"

    _divider()
    print(_row("HTTP",              f"{_comp_status(group['http'])}  {utils.GRAY}{group['http'] or 'none'}{utils.RESET}"))
    print(_row("HTTPS (SSL)",       f"{_comp_status(group['ssl'])}  {utils.GRAY}{group['ssl'] or 'none'}{utils.RESET}"))
    print(_row("HTTP->HTTPS redir", f"{_comp_status(group['redirect'])}  {utils.GRAY}{group['redirect'] or 'none'}{utils.RESET}"))
    _divider()
    print(_row("Listen IP",    f"{utils.YELLOW}{info.get('ip', '*')}{utils.RESET}"))
    print(_row("ServerName",   name_str))
    print(_row("ServerAlias",  alias_str))
    print(_row("DocumentRoot", f"{utils.WHITE}{info.get('doc_root', '-')}{utils.RESET}"))
    _divider()
    print(_row("Basic Auth",        _on(auth)))
    print(_row("Directory listing", _on(listing)))
    _divider()
    utils.pause()

# ── Enable / disable ───────────────────────────────────────────────────────────

def _enable_conf(site_conf):
    subprocess.run(["sudo", "a2ensite", site_conf], capture_output=True)

def _disable_conf(site_conf):
    subprocess.run(["sudo", "a2dissite", site_conf], capture_output=True)

def toggle_group(name, group):
    enabled = list_enabled()
    components = [c for c in [group["http"], group["ssl"], group["redirect"]] if c]
    if any(c in enabled for c in components):
        for c in components:
            _disable_conf(c)
        utils.log(f"{name} disabled. Reload Apache2 to apply.", "success")
    else:
        for c in components:
            _enable_conf(c)
        utils.log(f"{name} enabled. Reload Apache2 to apply.", "success")
    utils.pause()

# ── Add components ─────────────────────────────────────────────────────────────

def add_http_vhost(name, group):
    os.system("clear")
    utils.print_menu_name(f"Add HTTP - {name}")

    if group["redirect"]:
        utils.log(f"Redirect {group['redirect']} will be removed.", "info")
        if utils.choose(["yes", "no"], "Continue?") != "yes":
            return

    doc_root = f"/var/www/{name}"
    if group["ssl"]:
        info = _parse_conf(group["ssl"])
        if info["doc_root"] != "-":
            doc_root = info["doc_root"]

    conf_file = f"{name}.conf"
    subprocess.run(["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{conf_file}"],
                   input=_http_vhost(name, doc_root), text=True, capture_output=True)

    if group["redirect"]:
        _disable_conf(group["redirect"])
        subprocess.run(["sudo", "rm", f"{SITES_AVAILABLE}/{group['redirect']}"], capture_output=True)
        utils.log(f"Redirect removed.", "success")

    _enable_conf(conf_file)
    utils.log(f"{conf_file} created and enabled. Reload Apache2 to apply.", "success")
    utils.pause()

def add_ssl_vhost(name, group):
    os.system("clear")
    utils.print_menu_name(f"Add HTTPS - {name}")

    _enable_ssl_module()
    cert_path, key_path = _generate_self_signed_cert(name)
    if not cert_path:
        utils.pause()
        return

    doc_root = f"/var/www/{name}"
    if group["http"]:
        info = _parse_conf(group["http"])
        if info["doc_root"] != "-":
            doc_root = info["doc_root"]

    ssl_file = f"{name}-ssl.conf"
    subprocess.run(["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{ssl_file}"],
                   input=_ssl_vhost(name, doc_root, cert_path, key_path),
                   text=True, capture_output=True)
    _enable_conf(ssl_file)
    utils.log(f"{ssl_file} created and enabled.", "success")

    confirm = utils.choose(["yes", "no"], "Add HTTP->HTTPS redirect?")
    if confirm == "yes":
        if group["http"]:
            _disable_conf(group["http"])
            subprocess.run(["sudo", "rm", f"{SITES_AVAILABLE}/{group['http']}"], capture_output=True)
            utils.log(f"HTTP vhost removed.", "success")
        redirect_file = f"{name}-redirect.conf"
        info = _parse_conf(ssl_file)
        server_name = info["server_name"] if info["server_name"] != "-" else name
        subprocess.run(["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{redirect_file}"],
                       input=_redirect_vhost(server_name), text=True, capture_output=True)
        _enable_conf(redirect_file)
        utils.log(f"HTTP->HTTPS redirect created.", "success")

    utils.log("Reload Apache2 to apply.", "success")
    utils.pause()

def toggle_redirect(name, group):
    if group["redirect"]:
        if utils.choose(["yes", "no"], f"Remove redirect {group['redirect']}?", "error") != "yes":
            return
        _disable_conf(group["redirect"])
        subprocess.run(["sudo", "rm", f"{SITES_AVAILABLE}/{group['redirect']}"], capture_output=True)
        utils.log("Redirect removed. Reload Apache2 to apply.", "success")
    else:
        if not group["ssl"]:
            utils.log("No SSL vhost found. Add HTTPS first.", "error")
            utils.pause()
            return
        info = _parse_conf(group["ssl"])
        server_name = info["server_name"] if info["server_name"] != "-" else name
        redirect_file = f"{name}-redirect.conf"
        subprocess.run(["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{redirect_file}"],
                       input=_redirect_vhost(server_name), text=True, capture_output=True)
        _enable_conf(redirect_file)
        utils.log("Redirect created and enabled. Reload Apache2 to apply.", "success")
    utils.pause()

# ── Edit config ────────────────────────────────────────────────────────────────

def edit_site_config(name, group):
    confs = {}
    if group["http"]:
        confs["HTTP"] = group["http"]
    if group["ssl"]:
        confs["HTTPS (SSL)"] = group["ssl"]
    if not confs:
        utils.log("No vhost config found.", "error")
        utils.pause()
        return
    if len(confs) == 1:
        site_conf = list(confs.values())[0]
    else:
        label = utils.choose(list(confs.keys()), "Which vhost to configure?")
        if label is None:
            return
        site_conf = confs[label]
    _edit_vhost_config(site_conf)

def _edit_vhost_config(site_conf):
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name(f"Config - {site_conf}")

        info = _parse_conf(site_conf)
        aliases = _get_aliases(site_conf)
        print(f"  {utils.GRAY}{'Listen IP':<20}{utils.YELLOW}{info['ip']}{utils.RESET}")
        print(f"  {utils.GRAY}{'Port':<20}{utils.PURPLE}{info['port']}{utils.RESET}")
        print(f"  {utils.GRAY}{'ServerName':<20}{utils.YELLOW}{info['server_name']}{utils.RESET}")
        print(f"  {utils.GRAY}{'ServerAlias':<20}{utils.GRAY}{', '.join(aliases) or 'none'}{utils.RESET}")
        print(f"  {utils.GRAY}{'DocumentRoot':<20}{utils.WHITE}{info['doc_root']}{utils.RESET}")
        print()

        options = [
            "Listen IP", "Port", "ServerName", "ServerAlias", "DocumentRoot",
            "", "Advanced (nano)", "", "Back"
        ]
        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            new_ip = _pick_listen_ip()
            if new_ip is None:
                continue
            _write_conf(site_conf, _set_vhost_ip(_read_conf(site_conf), new_ip))
            utils.log(f"Listen IP set to {new_ip}. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 1:
            new_port = utils.ask_required("New port")
            if new_port is None:
                continue
            if not utils.check_port(new_port):
                utils.log("Invalid port.", "error")
                utils.pause()
                continue
            _write_conf(site_conf, _set_vhost_port(_read_conf(site_conf), new_port))
            utils.log(f"Port set to {new_port}. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 2:
            new_name = utils.ask_required("New ServerName")
            if new_name is None:
                continue
            _write_conf(site_conf, _set_directive(_read_conf(site_conf), "ServerName", new_name))
            utils.log(f"ServerName set to {new_name}. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 3:
            manage_aliases(site_conf)

        elif choice == 4:
            new_root = utils.ask_required("New DocumentRoot")
            if new_root is None:
                continue
            content = _read_conf(site_conf)
            updated = _set_directive(content, "DocumentRoot", new_root)
            updated = re.sub(r"<Directory\s+\S+>", f"<Directory {new_root}>", updated, count=1)
            _write_conf(site_conf, updated)
            utils.log(f"DocumentRoot set to {new_root}. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 6:
            subprocess.run(["sudo", "nano", f"{SITES_AVAILABLE}/{site_conf}"])

        elif choice == 8 or choice is None:
            return

        last = choice

# ── Edit page ──────────────────────────────────────────────────────────────────

def edit_page(name, group):
    main_conf = group["ssl"] or group["http"]
    if not main_conf:
        utils.log("No vhost config found.", "error")
        utils.pause()
        return
    info = _parse_conf(main_conf)
    if info["doc_root"] == "-":
        utils.log("Could not determine DocumentRoot.", "error")
        utils.pause()
        return
    subprocess.run(["sudo", "nano", f"{info['doc_root']}/index.html"])

# ── Logs ───────────────────────────────────────────────────────────────────────

def _show_log(log_path, title):
    os.system("clear")
    utils.print_menu_name(title)
    result = subprocess.run(["sudo", "cat", log_path], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        utils.log("Log is empty or not found.", "info")
    else:
        print(result.stdout)
    utils.pause()

def show_site_logs(name):
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name(f"Logs - {name}")
        choice = utils.show_menu(utils.create_menu(["Access log", "Error log", "", "Back"], last))
        if choice == 0:
            _show_log(f"{LOG_DIR}/{name}_access.log", f"Access log - {name}")
        elif choice == 1:
            _show_log(f"{LOG_DIR}/{name}_error.log", f"Error log - {name}")
        elif choice == 3 or choice is None:
            return
        last = choice

# ── Remove ─────────────────────────────────────────────────────────────────────

def remove_group(name, group):
    os.system("clear")
    utils.print_menu_name(f"Remove - {name}")

    components = [c for c in [group["http"], group["ssl"], group["redirect"]] if c]
    if not components:
        utils.log("Nothing to remove.", "info")
        utils.pause()
        return

    utils.log(f"Will remove: {', '.join(components)}", "info")
    if utils.choose(["yes", "no"], f"Remove all files for {name}?", "error") != "yes":
        return

    for c in components:
        _disable_conf(c)
        subprocess.run(["sudo", "rm", f"{SITES_AVAILABLE}/{c}"], capture_output=True)

    doc_root = f"/var/www/{name}"
    if utils.choose(["yes", "no"], f"Also delete DocumentRoot {doc_root}?", "error") == "yes":
        subprocess.run(["sudo", "rm", "-rf", doc_root], capture_output=True)
        utils.log(f"DocumentRoot {doc_root} deleted.", "success")

    utils.log(f"{name} removed. Reload Apache2 to apply.", "success")
    utils.pause()

# ── Add site ───────────────────────────────────────────────────────────────────

def add_site():
    os.system("clear")
    utils.print_menu_name("Add Site")

    name = utils.ask_required("Site name (e.g. example.com)")
    if name is None:
        return

    groups = _group_sites()
    if name in groups:
        existing = [f for f in groups[name].values() if f]
        utils.log(f"Site '{name}' already exists: {', '.join(existing)}", "error")
        utils.pause()
        return

    protocol = utils.choose(["HTTP", "HTTPS (SSL)", "Both"], "Protocol")
    if protocol is None:
        return

    doc_root = utils.ask(f"DocumentRoot (Enter for /var/www/{name})")
    if doc_root is None:
        return
    if not doc_root:
        doc_root = f"/var/www/{name}"

    subprocess.run(["sudo", "mkdir", "-p", doc_root], capture_output=True)
    subprocess.run(["sudo", "bash", "-c", f"cat > {doc_root}/index.html"],
                   input=_index_html(name), text=True, capture_output=True)

    if protocol in ("HTTP", "Both"):
        conf_file = f"{name}.conf"
        subprocess.run(["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{conf_file}"],
                       input=_http_vhost(name, doc_root), text=True, capture_output=True)
        _enable_conf(conf_file)
        utils.log(f"{conf_file} created.", "success")

    if protocol in ("HTTPS (SSL)", "Both"):
        _enable_ssl_module()
        cert_path, key_path = _generate_self_signed_cert(name)
        if cert_path:
            ssl_file = f"{name}-ssl.conf"
            subprocess.run(["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{ssl_file}"],
                           input=_ssl_vhost(name, doc_root, cert_path, key_path),
                           text=True, capture_output=True)
            _enable_conf(ssl_file)
            utils.log(f"{ssl_file} created.", "success")

            confirm = utils.choose(["yes", "no"], "Add HTTP->HTTPS redirect on port 80?")
            if confirm == "yes":
                if protocol == "Both":
                    _disable_conf(f"{name}.conf")
                    subprocess.run(["sudo", "rm", f"{SITES_AVAILABLE}/{name}.conf"], capture_output=True)
                redirect_file = f"{name}-redirect.conf"
                subprocess.run(["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{redirect_file}"],
                               input=_redirect_vhost(name), text=True, capture_output=True)
                _enable_conf(redirect_file)
                utils.log(f"{redirect_file} created.", "success")

    utils.log("Opening index.html in nano...", "info")
    subprocess.run(["sudo", "nano", f"{doc_root}/index.html"])

# ── Site menu ──────────────────────────────────────────────────────────────────

def site_menu(name, group):
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name(f"Site - {name}")

        group = _group_sites().get(name, {"http": None, "ssl": None, "redirect": None})

        enabled = list_enabled()
        components = [c for c in group.values() if c]
        any_enabled = any(c in enabled for c in components)
        toggle_label = "Disable" if any_enabled else "Enable"

        main_conf = group["ssl"] or group["http"]
        listing_label = (
            "Disable directory listing"
            if (main_conf and _directory_listing_enabled(main_conf))
            else "Enable directory listing"
        )

        can_add_http = not group["http"] and not group["redirect"]
        can_add_ssl = not group["ssl"]

        options = [
            "Show",                              # 0
            "Config",                            # 1
            "Edit page",                         # 2
            toggle_label,                        # 3
            "Add HTTP" if can_add_http else "",  # 4
            "Add HTTPS" if can_add_ssl else "",  # 5
            "HTTP->HTTPS redirect",              # 6
            listing_label,                       # 7
            "Auth",                              # 8
            "Logs",                              # 9
            "Remove",                            # 10
            "",                                  # 11
            "Back",                              # 12
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            show_site_details(name, group)
        elif choice == 1:
            edit_site_config(name, group)
        elif choice == 2:
            edit_page(name, group)
        elif choice == 3:
            toggle_group(name, group)
        elif choice == 4 and can_add_http:
            add_http_vhost(name, group)
        elif choice == 5 and can_add_ssl:
            add_ssl_vhost(name, group)
        elif choice == 6:
            toggle_redirect(name, group)
        elif choice == 7 and main_conf:
            toggle_directory_listing(main_conf)
        elif choice == 8 and main_conf:
            manage_auth(name, main_conf)
        elif choice == 9:
            show_site_logs(name)
        elif choice == 10:
            remove_group(name, group)
            return
        elif choice == 12 or choice is None:
            return

        last = choice

# ── Sites list ─────────────────────────────────────────────────────────────────

def manage_sites():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Sites")

        groups = _group_sites()
        enabled = list_enabled()
        names = sorted(groups.keys())

        site_options = []
        for name in names:
            g = groups[name]
            components = [c for c in g.values() if c]
            any_enabled = any(c in enabled for c in components)
            marker = "[on] " if any_enabled else "[off]"
            tags = []
            if g["http"]:     tags.append("HTTP")
            if g["ssl"]:      tags.append("SSL")
            if g["redirect"]: tags.append("->")
            tag_str = "  " + " ".join(tags) if tags else ""
            site_options.append(f"{marker} {name}{tag_str}")

        options = site_options + ["", "Add site", "", "Back"]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice is None:
            return

        add_index = len(names) + 1
        back_index = len(names) + 3

        if choice < len(names):
            site_menu(names[choice], groups[names[choice]])
        elif choice == add_index:
            add_site()
        elif choice == back_index:
            return

        last = choice
