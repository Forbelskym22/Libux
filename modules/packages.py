import os
import subprocess
from simple_term_menu import TerminalMenu
from modules import utils


# (apt_package, display_name, description)
PACKAGES = [
    ("apache2",             "Apache2",             "HTTP server"),
    ("openssh-server",      "OpenSSH server",      "SSH remote access"),
    ("mariadb-server",      "MariaDB",             "Database server"),
    ("phpmyadmin",          "phpMyAdmin",          "Web UI for MariaDB (needs Apache2)"),
    ("isc-dhcp-server",     "ISC DHCP server",     "DHCP server"),
    ("iptables-persistent", "iptables-persistent", "Persists firewall rules across reboots"),
    ("quota",               "quota",               "Disk quota tools (quotaon, repquota, setquota)"),
]


def _is_installed(pkg):
    return utils.is_pkg_installed(pkg)


def _label(display, desc):
    return f"{display:<20} {desc}"


def _controls_hint():
    print()
    print(f"  {utils.WHITE}Controls:{utils.RESET}")
    print(f"    {utils.YELLOW}↑ / ↓{utils.GRAY}        move{utils.RESET}")
    print(f"    {utils.YELLOW}Space / Tab{utils.GRAY}  tick / untick a package{utils.RESET}")
    print(f"    {utils.YELLOW}Enter{utils.GRAY}        confirm{utils.RESET}")
    print(f"    {utils.YELLOW}Ctrl+C{utils.GRAY}       cancel{utils.RESET}")
    print()


def _multi_pick(items, title, empty_msg):
    """
    items: list of (pkg, display, desc)
    Returns list of picked items, or [] if cancelled / nothing selected.
    """
    if not items:
        os.system("clear")
        utils.print_menu_name(title)
        utils.log(empty_msg, "info")
        utils.pause()
        return []

    os.system("clear")
    utils.print_menu_name(title)
    _controls_hint()

    options = [_label(display, desc) for _, display, desc in items]
    menu = TerminalMenu(
        options,
        multi_select=True,
        show_multi_select_hint=True,
        multi_select_select_on_accept=False,
        multi_select_empty_ok=True,
        cycle_cursor=True,
        clear_screen=False,
        menu_cursor_style=utils.MENU_CURSOR_STYLE,
    )
    try:
        chosen = menu.show()
    except KeyboardInterrupt:
        return []
    if not chosen:
        return []
    return [items[i] for i in chosen]


def _summarize(label, color, items):
    print(f"  {color}{label}:{utils.RESET}")
    for _, display, _ in items:
        print(f"    {utils.WHITE}{display}{utils.RESET}")
    print()


# Packages whose removal must NOT prompt for destructive confirmations
# (e.g. dropping databases). DEBIAN_FRONTEND=noninteractive handles the rest.
_NONINTERACTIVE_ENV = {**os.environ, "DEBIAN_FRONTEND": "noninteractive"}


def _install_flow():
    not_installed = [(pkg, display, desc) for pkg, display, desc in PACKAGES if not _is_installed(pkg)]
    picked = _multi_pick(not_installed, "Install packages", "All supported packages are already installed.")
    if not picked:
        return

    # phpmyadmin needs apache2
    picked_names = {p[0] for p in picked}
    if "phpmyadmin" in picked_names:
        apache_ok = _is_installed("apache2") or "apache2" in picked_names
        if not apache_ok:
            utils.log("phpMyAdmin needs Apache2 to serve its web UI.", "error")
            utils.log("Select Apache2 as well, or install it separately first.", "info")
            utils.pause()
            return

    os.system("clear")
    utils.print_menu_name("Install packages - confirm")
    print()
    _summarize("Install", utils.GREEN, picked)
    if utils.choose(["yes", "no"], "Install these packages?") != "yes":
        return

    os.system("clear")
    utils.print_menu_name("Install packages - running")
    utils.log("Running apt update...", "info")
    subprocess.run(["sudo", "apt", "update"], capture_output=True, text=True)

    for pkg, display, _ in picked:
        utils.log(f"Installing {display} ({pkg})...", "info")
        # phpmyadmin needs to be interactive for its debconf config wizard;
        # everything else runs noninteractive so nothing can hang.
        if pkg == "phpmyadmin":
            subprocess.run(["sudo", "apt", "install", pkg, "-y"])
        else:
            subprocess.run(
                ["sudo", "-E", "apt-get", "install", "-y", pkg],
                env=_NONINTERACTIVE_ENV,
            )
        if _is_installed(pkg):
            utils.log(f"{display} installed.", "success")
        else:
            utils.log(f"{display} installation failed or was cancelled.", "error")
    utils.pause()


def _remove_flow():
    installed = [(pkg, display, desc) for pkg, display, desc in PACKAGES if _is_installed(pkg)]
    picked = _multi_pick(installed, "Remove packages", "No supported packages are installed.")
    if not picked:
        return

    os.system("clear")
    utils.print_menu_name("Remove packages - confirm")
    print()
    _summarize("Remove", utils.RED, picked)
    print(f"  {utils.GRAY}This will run: apt-get purge -y <pkg> and then apt-get autoremove.{utils.RESET}")
    print(f"  {utils.GRAY}Config files in /etc will be removed as well.{utils.RESET}")
    print()
    if utils.choose(["yes", "no"], "Remove these packages?", "error") != "yes":
        return

    os.system("clear")
    utils.print_menu_name("Remove packages - running")
    for pkg, display, _ in picked:
        utils.log(f"Removing {display} ({pkg})...", "info")
        # Noninteractive purge so mariadb / phpmyadmin can't hang on
        # dbconfig-common or "drop database?" prompts.
        subprocess.run(
            ["sudo", "-E", "apt-get", "purge", "-y", pkg],
            env=_NONINTERACTIVE_ENV,
        )
        if not _is_installed(pkg):
            utils.log(f"{display} removed.", "success")
        else:
            utils.log(f"Failed to remove {display}.", "error")

    utils.log("Cleaning up orphaned dependencies...", "info")
    subprocess.run(
        ["sudo", "-E", "apt-get", "autoremove", "-y"],
        env=_NONINTERACTIVE_ENV,
    )
    utils.pause()


def _show_status():
    os.system("clear")
    utils.print_menu_name("Packages - status")
    print()
    for pkg, display, desc in PACKAGES:
        installed = _is_installed(pkg)
        tag_color = utils.GREEN if installed else utils.GRAY
        tag = "installed" if installed else "not installed"
        print(f"  {utils.WHITE}{display:<20}{utils.GRAY}{desc:<42}{tag_color}[{tag}]{utils.RESET}")
    print()
    utils.pause()


def manage_packages():
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Packages")

        options = [
            "Status",   # 0
            "Install",  # 1
            "Remove",   # 2
            "",         # 3
            "Back",     # 4
        ]

        menu = utils.create_menu(options, last)
        choice = utils.show_menu(menu)

        if choice == 0:
            _show_status()
        elif choice == 1:
            _install_flow()
        elif choice == 2:
            _remove_flow()
        elif choice == 4 or choice is None:
            return

        last = choice
