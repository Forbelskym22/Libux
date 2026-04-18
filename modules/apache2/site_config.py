import os
import re
import subprocess
from modules import utils
from .shared import SITES_AVAILABLE
from .site_helpers import (
    parse_conf, read_conf, write_conf,
    set_vhost_port, set_vhost_ip, set_directive,
    pick_listen_ip,
)

# ── ServerAlias ────────────────────────────────────────────────────────────────

def get_aliases(site_conf):
    for line in read_conf(site_conf).splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("serveralias"):
            return stripped.split()[1:]
    return []

def manage_aliases(site_conf):
    while True:
        os.system("clear")
        utils.print_menu_name(f"ServerAlias - {site_conf}")

        aliases = get_aliases(site_conf)
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
            content = read_conf(site_conf)
            if re.search(r"ServerAlias", content, re.IGNORECASE):
                new_content = set_directive(content, "ServerAlias", " ".join(aliases))
            else:
                new_content = re.sub(
                    r"(ServerName\s+\S+)", rf"\1\n    ServerAlias {alias}",
                    content, count=1, flags=re.IGNORECASE
                )
            write_conf(site_conf, new_content)
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
            content = read_conf(site_conf)
            new_content = (
                set_directive(content, "ServerAlias", " ".join(aliases))
                if aliases
                else re.sub(r"\n?\s*ServerAlias\s+.+", "", content, flags=re.IGNORECASE)
            )
            write_conf(site_conf, new_content)
            utils.log(f"Alias {alias} removed. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 3 or choice is None:
            break

# ── Directory listing ──────────────────────────────────────────────────────────

def directory_listing_enabled(site_conf):
    m = re.search(r"Options\s+([^\n]+)", read_conf(site_conf), re.IGNORECASE)
    return bool(m and "Indexes" in m.group(1))

def toggle_directory_listing(site_conf):
    content = read_conf(site_conf)
    if directory_listing_enabled(site_conf):
        new_content = re.sub(r"(Options\s+[^\n]*)Indexes\s*", r"\1", content, flags=re.IGNORECASE)
        write_conf(site_conf, new_content)
        utils.log("Directory listing disabled. Reload Apache2 to apply.", "success")
    else:
        new_content = re.sub(r"(Options\s+)", r"\1Indexes ", content, count=1, flags=re.IGNORECASE)
        write_conf(site_conf, new_content)
        utils.log("Directory listing enabled. Reload Apache2 to apply.", "success")
    utils.pause()

# ── Vhost config editor ────────────────────────────────────────────────────────

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

        info = parse_conf(site_conf)
        aliases = get_aliases(site_conf)
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
        choice = utils.show_menu(utils.create_menu(options, last))

        if choice == 0:
            new_ip = pick_listen_ip()
            if new_ip is None:
                continue
            write_conf(site_conf, set_vhost_ip(read_conf(site_conf), new_ip))
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
            write_conf(site_conf, set_vhost_port(read_conf(site_conf), new_port))
            utils.log(f"Port set to {new_port}. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 2:
            new_name = utils.ask_required("New ServerName")
            if new_name is None:
                continue
            write_conf(site_conf, set_directive(read_conf(site_conf), "ServerName", new_name))
            utils.log(f"ServerName set to {new_name}. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 3:
            manage_aliases(site_conf)

        elif choice == 4:
            new_root = utils.ask_required("New DocumentRoot")
            if new_root is None:
                continue
            content = read_conf(site_conf)
            updated = set_directive(content, "DocumentRoot", new_root)
            updated = re.sub(r"<Directory\s+\S+>", f"<Directory {new_root}>", updated, count=1)
            write_conf(site_conf, updated)
            utils.log(f"DocumentRoot set to {new_root}. Reload Apache2 to apply.", "success")
            utils.pause()

        elif choice == 6:
            subprocess.run(["sudo", "nano", f"{SITES_AVAILABLE}/{site_conf}"])

        elif choice == 8 or choice is None:
            return

        last = choice
