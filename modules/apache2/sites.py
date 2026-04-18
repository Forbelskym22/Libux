import os
import subprocess
from modules import utils
from .shared import SITES_AVAILABLE, LOG_DIR
from .site_helpers import (
    list_available, list_enabled,
    group_sites, parse_conf,
    enable_conf, disable_conf,
    http_vhost, index_html,
    on, row, divider,
)
from .site_auth import auth_enabled, manage_auth
from .site_ssl import add_ssl_vhost, toggle_redirect, generate_self_signed_cert, enable_ssl_module
from .site_config import edit_site_config, directory_listing_enabled, toggle_directory_listing, get_aliases

# ── Show ───────────────────────────────────────────────────────────────────────

def show_site_details(name, group):
    os.system("clear")
    utils.print_menu_name(f"Site - {name}")

    enabled = list_enabled()
    main_conf = group["ssl"] or group["http"]
    info = parse_conf(main_conf) if main_conf else {}
    aliases = get_aliases(main_conf) if main_conf else []
    auth = auth_enabled(main_conf) if main_conf else False
    listing = directory_listing_enabled(main_conf) if main_conf else False

    def _comp(conf):
        if not conf:
            return f"{utils.GRAY}none{utils.RESET}"
        return f"{utils.GREEN}on {utils.RESET}" if conf in enabled else f"{utils.GRAY}off{utils.RESET}"

    name_str = (
        f"{utils.YELLOW}{info.get('server_name')}{utils.RESET}"
        if info.get("server_name") not in (None, "-")
        else f"{utils.GRAY}not set{utils.RESET}"
    )
    alias_str = f"{utils.GRAY}{', '.join(aliases)}{utils.RESET}" if aliases else f"{utils.GRAY}none{utils.RESET}"

    divider()
    print(row("HTTP",              f"{_comp(group['http'])}  {utils.GRAY}{group['http'] or 'none'}{utils.RESET}"))
    print(row("HTTPS (SSL)",       f"{_comp(group['ssl'])}  {utils.GRAY}{group['ssl'] or 'none'}{utils.RESET}"))
    print(row("HTTP->HTTPS redir", f"{_comp(group['redirect'])}  {utils.GRAY}{group['redirect'] or 'none'}{utils.RESET}"))
    divider()
    print(row("Listen IP",    f"{utils.YELLOW}{info.get('ip', '*')}{utils.RESET}"))
    print(row("ServerName",   name_str))
    print(row("ServerAlias",  alias_str))
    print(row("DocumentRoot", f"{utils.WHITE}{info.get('doc_root', '-')}{utils.RESET}"))
    divider()
    print(row("Basic Auth",        on(auth)))
    print(row("Directory listing", on(listing)))
    divider()
    utils.pause()

# ── Enable / disable group ─────────────────────────────────────────────────────

def toggle_group(name, group):
    enabled = list_enabled()
    components = [c for c in group.values() if c]
    if any(c in enabled for c in components):
        for c in components:
            disable_conf(c)
        utils.log(f"{name} disabled. Reload Apache2 to apply.", "success")
    else:
        for c in components:
            enable_conf(c)
        utils.log(f"{name} enabled. Reload Apache2 to apply.", "success")
    utils.pause()

# ── Add HTTP vhost ─────────────────────────────────────────────────────────────

def add_http_vhost(name, group):
    os.system("clear")
    utils.print_menu_name(f"Add HTTP - {name}")

    if group["redirect"]:
        utils.log(f"Redirect {group['redirect']} will be removed.", "info")
        if utils.choose(["yes", "no"], "Continue?") != "yes":
            return

    doc_root = f"/var/www/{name}"
    if group["ssl"]:
        info = parse_conf(group["ssl"])
        if info["doc_root"] != "-":
            doc_root = info["doc_root"]

    conf_file = f"{name}.conf"
    subprocess.run(
        ["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{conf_file}"],
        input=http_vhost(name, doc_root), text=True, capture_output=True
    )

    if group["redirect"]:
        disable_conf(group["redirect"])
        subprocess.run(["sudo", "rm", f"{SITES_AVAILABLE}/{group['redirect']}"], capture_output=True)
        utils.log("Redirect removed.", "success")

    enable_conf(conf_file)
    utils.log(f"{conf_file} created and enabled. Reload Apache2 to apply.", "success")
    utils.pause()

# ── Edit page ──────────────────────────────────────────────────────────────────

def edit_page(name, group):
    main_conf = group["ssl"] or group["http"]
    if not main_conf:
        utils.log("No vhost config found.", "error")
        utils.pause()
        return
    info = parse_conf(main_conf)
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

# ── Remove group ───────────────────────────────────────────────────────────────

def remove_group(name, group):
    os.system("clear")
    utils.print_menu_name(f"Remove - {name}")

    components = [c for c in group.values() if c]
    if not components:
        utils.log("Nothing to remove.", "info")
        utils.pause()
        return

    utils.log(f"Will remove: {', '.join(components)}", "info")
    if utils.choose(["yes", "no"], f"Remove all files for {name}?", "error") != "yes":
        return

    for c in components:
        disable_conf(c)
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

    groups = group_sites()
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
    subprocess.run(
        ["sudo", "bash", "-c", f"cat > {doc_root}/index.html"],
        input=index_html(name), text=True, capture_output=True
    )

    if protocol in ("HTTP", "Both"):
        conf_file = f"{name}.conf"
        subprocess.run(
            ["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{conf_file}"],
            input=http_vhost(name, doc_root), text=True, capture_output=True
        )
        enable_conf(conf_file)
        utils.log(f"{conf_file} created.", "success")

    if protocol in ("HTTPS (SSL)", "Both"):
        enable_ssl_module()
        cert_path, key_path = generate_self_signed_cert(name)
        if cert_path:
            from .site_helpers import ssl_vhost, redirect_vhost
            ssl_file = f"{name}-ssl.conf"
            subprocess.run(
                ["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{ssl_file}"],
                input=ssl_vhost(name, doc_root, cert_path, key_path),
                text=True, capture_output=True
            )
            enable_conf(ssl_file)
            utils.log(f"{ssl_file} created.", "success")

            if utils.choose(["yes", "no"], "Add HTTP->HTTPS redirect on port 80?") == "yes":
                if protocol == "Both":
                    disable_conf(f"{name}.conf")
                    subprocess.run(["sudo", "rm", f"{SITES_AVAILABLE}/{name}.conf"], capture_output=True)
                redirect_file = f"{name}-redirect.conf"
                subprocess.run(
                    ["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{redirect_file}"],
                    input=redirect_vhost(name), text=True, capture_output=True
                )
                enable_conf(redirect_file)
                utils.log(f"{redirect_file} created.", "success")

    utils.log("Opening index.html in nano...", "info")
    subprocess.run(["sudo", "nano", f"{doc_root}/index.html"])

# ── Site menu ──────────────────────────────────────────────────────────────────

def site_menu(name, group):
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name(f"Site - {name}")

        group = group_sites().get(name, {"http": None, "ssl": None, "redirect": None})

        enabled = list_enabled()
        components = [c for c in group.values() if c]
        any_enabled = any(c in enabled for c in components)
        toggle_label = "Disable" if any_enabled else "Enable"

        main_conf = group["ssl"] or group["http"]
        listing_label = (
            "Disable directory listing"
            if (main_conf and directory_listing_enabled(main_conf))
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

        choice = utils.show_menu(utils.create_menu(options, last))

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

        groups = group_sites()
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
        choice = utils.show_menu(utils.create_menu(options, last))

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
