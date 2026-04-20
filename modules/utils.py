import shutil
import subprocess
from simple_term_menu import TerminalMenu
import ipaddress

# simple_term_menu cursor style (globally used)
MENU_CURSOR_STYLE = ("fg_purple", "bold")

#colors
RED = "\033[91m"
GREEN = "\033[92m"
PURPLE = "\033[38;5;135m"
WHITE = "\033[97m"

PINK = "\033[38;5;213m"
YELLOW = "\033[38;5;226m"
ORANGE = "\033[38;5;208m"
GRAY = "\033[38;5;240m"
RESET = "\033[0m"
PREFIX = f"{PURPLE}[Libux]{RESET}"

word_colors = {
        "ACCEPT": GREEN,
        "DROP": RED,
        "REJECT": RED,
        "all": GRAY,
        "tcp": WHITE,
        "udp": WHITE,
        "icmp": WHITE,
        "lo": YELLOW
    }

VERBOSE = False


def create_menu(options, cursor_index=0):
    return TerminalMenu(
        options,
        cursor_index=cursor_index,
        cycle_cursor=True,
        clear_screen=False,
        skip_empty_entries=True,
        menu_cursor_style=MENU_CURSOR_STYLE
    )


def run_cmd(cmd):
    if VERBOSE:
        log(f"Running: {' '.join(cmd)}", "info")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"Command failed: {result.stderr.strip()}", "error")
        return False
    return True

def ask(prompt):
    try:
        return input(f"{WHITE}{prompt}{GRAY} (Enter to skip): {RESET}").strip()
    except KeyboardInterrupt:
        return None
    except UnicodeDecodeError:
        log("Input encoding error. Use ASCII characters only.", "error")
        return ask(prompt)

def ask_required(prompt):
    while True:
        try:
            value = input(f"{WHITE}{prompt}: {RESET}").strip()
            if not value:
                log("This field is required.", "error")
                continue
            return value
        except KeyboardInterrupt:
            return None
        except UnicodeDecodeError:
            log("Input encoding error. Use ASCII characters only.", "error")


def pause():
    try:
        input(f"\n{GRAY}Press Enter to continue...{RESET}")
    except KeyboardInterrupt:
        pass
    except UnicodeDecodeError:
        pass

def ask_ip(msg="IP/subnet"):
    while True:
        src_ip = ask(msg)
        if src_ip is None: return
        if not src_ip or check_ip(src_ip): return src_ip
        log("Invalid IP/subnet.", "error")


def check_ip(ip):
    try:
        ipaddress.ip_network(ip, strict = False)
        return True
    except ValueError:
        return False

def check_port(port):
    return port.isdigit() and (0 < int(port) < 65536)

def choose(options, message="", type= "info", cursor_index=0):
    if not options:
        log("No options to choose from", "error")
        return None
    if message:
        log(message, type)
    menu = TerminalMenu(options, cursor_index=cursor_index, cycle_cursor=True, clear_screen=False, menu_cursor_style=MENU_CURSOR_STYLE)
    choice = show_menu(menu)
    if choice is None:
        return None
    return options[choice]


def pick_interface(text="", exclude=None):
    cmd = ["ip", "-o", "link", "show"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    interfaces = [line.split()[1].strip(":") for line in result.stdout.splitlines()]

    if exclude:
        interfaces = [i for i in interfaces if i not in exclude]

    message = "choose interface"
    if text:
        message = message + f" ({text})"
    log(message, "info")

    menu = TerminalMenu(interfaces, cycle_cursor=True, clear_screen=False, menu_cursor_style=MENU_CURSOR_STYLE)
    choice = show_menu(menu)
    if choice is None:
        return None
    return interfaces[choice]

def is_binary_installed(service_name):
    """
    Function used to check if the service is installed on our device.
    """
    return shutil.which(service_name) is not None

def log(message,msg_type="info"):
    """
    Writes out a message to the Teminal
    msg_types: 'info' (default), 'success' (green), 'error' (red)
    """
    if(msg_type == "success"):
        print(f"{PREFIX} {GREEN}{message}{RESET}")
    elif(msg_type == "error"):
        print(f"{PREFIX} {RED}{message}{RESET}")
    else:
        print(f"{PREFIX} {WHITE}{message}{RESET}")


def show_menu(menu):
    """
    Wrapper around menu.show() that treats Ctrl+C as cancel (returns None).
    """
    try:
        return menu.show()
    except KeyboardInterrupt:
        return None

def print_menu_name(title):
    """
    Print menu header with purple highlight
    """
    print(f"{PURPLE}---{RESET} {WHITE}{title}{RESET} {PURPLE}---{RESET} {GRAY}Ctrl+C (exit){RESET}")

_last_path = None  # remembered across pick_path calls
_QUICK_DIRS = ["/etc", "/var/log", "/var/www", "/tmp", "/home", "/root", "/"]


def _human_size(n):
    for unit in ("B", "K", "M", "G", "T"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}P"


def _preview_entry(full_path):
    """Return multi-line info about a filesystem entry for the preview pane."""
    import os
    import stat as stat_mod
    import time
    try:
        st = os.lstat(full_path)
    except OSError as e:
        return f"error: {e}"

    mode_str = stat_mod.filemode(st.st_mode)
    octal = oct(st.st_mode)[-3:]
    lines = []

    if stat_mod.S_ISLNK(st.st_mode):
        try:
            target = os.readlink(full_path)
        except OSError:
            target = "?"
        lines.append(f"type:    symlink")
        lines.append(f"target:  {target}")
        try:
            tst = os.stat(full_path)  # follows link
            lines.append(f"points to: {stat_mod.filemode(tst.st_mode)}")
        except OSError:
            lines.append("points to: (broken)")
    elif stat_mod.S_ISDIR(st.st_mode):
        lines.append("type:    directory")
        try:
            count = len(os.listdir(full_path))
            lines.append(f"entries: {count}")
        except PermissionError:
            lines.append("entries: (permission denied)")
    elif stat_mod.S_ISREG(st.st_mode):
        lines.append("type:    file")
        lines.append(f"size:    {_human_size(st.st_size)}")
        if os.access(full_path, os.X_OK):
            lines.append("         (executable)")
    else:
        lines.append("type:    special")

    lines.append(f"mode:    {mode_str}  ({octal})")
    lines.append(f"uid/gid: {st.st_uid}/{st.st_gid}")
    try:
        mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
        lines.append(f"mtime:   {mtime}")
    except (ValueError, OSError):
        pass
    return "\n".join(lines)


def pick_path(start="/", dirs_only=False):
    """
    Interactive file/directory picker.
    Quick-start menu offers last-used path, home, common dirs, or manual entry.
    Browse mode shows preview pane with mode/size/mtime for the highlighted entry.
    Returns selected path or None on Ctrl+C.
    """
    global _last_path
    import os

    # ── Quick-start menu ───────────────────────────────────────────────────────
    os.system("clear")
    print_menu_name("Select path")

    home = os.path.expanduser("~")
    quick_options = []
    quick_targets = []
    seen = set()

    def _add(label, kind, value):
        key = (kind, value)
        if key in seen:
            return
        seen.add(key)
        quick_options.append(label)
        quick_targets.append((kind, value))

    if _last_path and os.path.exists(_last_path):
        start_from = _last_path if os.path.isdir(_last_path) else os.path.dirname(_last_path)
        _add(f"Last used:      {_last_path}", "browse", start_from)

    if os.path.isdir(home):
        _add(f"Home:           {home}", "browse", home)

    for d in _QUICK_DIRS:
        if os.path.isdir(d):
            _add(f"Go to:          {d}", "browse", d)

    _add(f"Browse from:    {start}", "browse", start)
    _add("Type path manually", "type", None)

    idx = show_menu(create_menu(quick_options))
    if idx is None:
        return None

    mode, value = quick_targets[idx]

    # ── Manual entry ───────────────────────────────────────────────────────────
    if mode == "type":
        os.system("clear")
        print_menu_name("Enter path")
        while True:
            print()
            try:
                typed = input(f"{WHITE}Path: {RESET}").strip()
            except KeyboardInterrupt:
                return None
            if not typed:
                log("Path cannot be empty. Try again or press Ctrl+C to cancel.", "error")
                continue
            typed = os.path.expanduser(typed)
            if os.path.exists(typed):
                _last_path = typed
                return typed
            log(f"Path '{typed}' does not exist. Try again or press Ctrl+C to cancel.", "error")

    # ── Browse ─────────────────────────────────────────────────────────────────
    current = value
    while True:
        os.system("clear")
        print_menu_name(f"Browse - {current}")

        try:
            entries = sorted(os.listdir(current))
        except PermissionError:
            log("Permission denied.", "error")
            current = os.path.dirname(current) or "/"
            continue
        except FileNotFoundError:
            current = "/"
            continue

        items = []  # list of (label, kind, full_path)
        for e in entries:
            full = os.path.join(current, e)
            try:
                is_link = os.path.islink(full)
                is_dir  = os.path.isdir(full)   # follows symlink
                is_file = os.path.isfile(full)
            except OSError:
                continue

            if dirs_only and not is_dir:
                continue

            if is_link:
                try:
                    target = os.readlink(full)
                except OSError:
                    target = "?"
                label = f"{e}@ -> {target}"
                kind  = "dir" if is_dir else "file"
            elif is_dir:
                label = f"{e}/"
                kind  = "dir"
            elif is_file:
                try:
                    size = _human_size(os.stat(full).st_size)
                    exe  = os.access(full, os.X_OK)
                except OSError:
                    size, exe = "?", False
                label = f"{e}{'*' if exe else ''}    {size}"
                kind  = "file"
            else:
                label = e
                kind  = "file"

            items.append((label, kind, full))

        # dirs first, then files; alphabetic within each group
        items.sort(key=lambda x: (x[1] != "dir", x[0].lower()))

        header = [(f"[ Select: {current} ]", "select", current)]
        if current != "/":
            header.append(("..  (parent)", "parent", os.path.dirname(current) or "/"))

        all_items = header + items
        options   = [lbl for lbl, _, _ in all_items]

        label_to_path = {lbl: full for lbl, k, full in all_items if k != "select"}
        def _preview(entry_label):
            target = label_to_path.get(entry_label)
            if target is None:
                return f"Current directory:\n{current}"
            return _preview_entry(target)

        menu = TerminalMenu(
            options,
            cycle_cursor=True,
            clear_screen=False,
            menu_cursor_style=MENU_CURSOR_STYLE,
            preview_command=_preview,
            preview_size=0.4,
        )
        try:
            sel_idx = menu.show()
        except KeyboardInterrupt:
            return None
        if sel_idx is None:
            return None

        _, kind, path = all_items[sel_idx]
        if kind == "select":
            _last_path = current
            return current
        elif kind == "parent":
            current = path
        elif kind == "dir":
            current = path
        else:
            _last_path = path
            return path
