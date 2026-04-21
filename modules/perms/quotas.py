import os
import re
import subprocess
from modules import utils
from .shared import FSTAB

# ── Filesystem helpers ─────────────────────────────────────────────────────────

def get_filesystems():
    """Returns list of dicts: {device, mountpoint, fstype, options}"""
    result = subprocess.run(["cat", "/proc/mounts"], capture_output=True, text=True)
    fs = []
    skip = {"tmpfs", "proc", "sysfs", "devpts", "cgroup", "cgroup2",
            "pstore", "debugfs", "securityfs", "fusectl", "bpf",
            "hugetlbfs", "mqueue", "tracefs", "devtmpfs", "overlay"}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        if parts[2] in skip or parts[1].startswith("/sys") or parts[1].startswith("/proc"):
            continue
        fs.append({"device": parts[0], "mountpoint": parts[1],
                   "fstype": parts[2], "options": parts[3]})
    return fs

def quota_enabled(fs):
    return "usrquota" in fs["options"]

def pick_filesystem(prompt="Select filesystem"):
    mounts = get_filesystems()
    if not mounts:
        utils.log("No suitable filesystems found.", "error")
        utils.pause()
        return None
    labels = [
        f"{'[quota]' if quota_enabled(m) else '       '} {m['mountpoint']}  ({m['device']}, {m['fstype']})"
        for m in mounts
    ]
    choice = utils.choose(labels, prompt)
    if choice is None:
        return None
    return mounts[labels.index(choice)]

# ── Show usage ─────────────────────────────────────────────────────────────────

def show_quota_usage():
    os.system("clear")
    utils.print_menu_name("Quota usage")
    result = subprocess.run(["sudo", "repquota", "-a"], capture_output=True, text=True)
    if result.returncode != 0:
        utils.log("No quotas are enabled on any filesystem.", "error")
        if utils.choose(["yes", "no"], "Enable quotas now?") == "yes":
            enable_quotas()
        return
    print(result.stdout or "No quota data.")
    utils.pause()

# ── Set user quota ─────────────────────────────────────────────────────────────

def set_user_quota():
    os.system("clear")
    utils.print_menu_name("Set user quota")

    fs = pick_filesystem("Select filesystem")
    if fs is None:
        return
    if not quota_enabled(fs):
        utils.log(f"Quotas not enabled on {fs['mountpoint']}. Enable them first.", "error")
        utils.pause()
        return

    aquota = os.path.join(fs["mountpoint"], "aquota.user")
    if not os.path.exists(aquota):
        utils.log(f"Quota file {aquota} is missing — quotacheck hasn't run successfully.", "error")
        utils.log(f"Run 'Enable quotas' again; root filesystem may need a reboot first.", "info")
        utils.pause()
        return

    username = utils.ask_required("Username")
    if username is None:
        return

    print(f"\n  {utils.GRAY}Soft limit — warning threshold (e.g. 1G, 500M, 0 = no limit){utils.RESET}")
    soft = utils.ask_required("Soft limit")
    if soft is None:
        return

    print(f"\n  {utils.GRAY}Hard limit — absolute maximum (e.g. 2G, 0 = no limit){utils.RESET}")
    hard = utils.ask_required("Hard limit")
    if hard is None:
        return

    result = subprocess.run(
        ["sudo", "setquota", "-u", username, soft, hard, "0", "0", fs["mountpoint"]],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to set quota.", "error")
    else:
        utils.log(f"Quota set for '{username}' on {fs['mountpoint']}.", "success")
    utils.pause()

# ── Enable / disable quotas ────────────────────────────────────────────────────

def enable_quotas():
    os.system("clear")
    utils.print_menu_name("Enable quotas")

    fs = pick_filesystem("Select filesystem")
    if fs is None:
        return
    if quota_enabled(fs):
        utils.log(f"Quotas already enabled on {fs['mountpoint']}.", "info")
        utils.pause()
        return

    # Update fstab
    result = subprocess.run(["sudo", "cat", FSTAB], capture_output=True, text=True)
    content = result.stdout
    mp = re.escape(fs["mountpoint"])
    new_content = re.sub(
        rf"(\s+{mp}\s+\S+\s+)(\S+)",
        lambda m: m.group(1) + m.group(2) + ",usrquota",
        content
    )
    subprocess.run(["sudo", "bash", "-c", f"cat > {FSTAB}"],
                   input=new_content, text=True, capture_output=True)

    remount = subprocess.run(["sudo", "mount", "-o", "remount", fs["mountpoint"]],
                             capture_output=True, text=True)
    if remount.returncode != 0:
        utils.log(f"Remount failed: {remount.stderr.strip()}", "error")
        utils.log(f"The '{fs['mountpoint']}' filesystem may need a reboot for usrquota to take effect.", "info")
        utils.pause()
        return

    qcheck = subprocess.run(["sudo", "quotacheck", "-cum", fs["mountpoint"]],
                            capture_output=True, text=True)
    if qcheck.returncode != 0:
        utils.log(f"quotacheck failed: {qcheck.stderr.strip() or qcheck.stdout.strip()}", "error")
        if fs["mountpoint"] == "/":
            utils.log("Root filesystem usually needs a reboot (or single-user mode) before quotacheck can create aquota.user.", "info")
        utils.pause()
        return

    result = subprocess.run(["sudo", "quotaon", fs["mountpoint"]], capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to enable quotas.", "error")
    else:
        utils.log(f"Quotas enabled on {fs['mountpoint']}.", "success")
    utils.pause()

def disable_quotas():
    os.system("clear")
    utils.print_menu_name("Disable quotas")

    fs = pick_filesystem("Select filesystem")
    if fs is None:
        return
    if not quota_enabled(fs):
        utils.log(f"Quotas not enabled on {fs['mountpoint']}.", "info")
        utils.pause()
        return

    subprocess.run(["sudo", "quotaoff", fs["mountpoint"]], capture_output=True)

    result = subprocess.run(["sudo", "cat", FSTAB], capture_output=True, text=True)
    new_content = re.sub(r",usrquota", "", result.stdout)
    subprocess.run(["sudo", "bash", "-c", f"cat > {FSTAB}"],
                   input=new_content, text=True, capture_output=True)

    utils.log(f"Quotas disabled on {fs['mountpoint']}.", "success")
    utils.pause()

# ── Quotas menu ────────────────────────────────────────────────────────────────

def _ensure_quota_installed():
    if utils.is_pkg_installed("quota"):
        return True
    utils.log("The 'quota' package is not installed (needed for quotaon, repquota, setquota).", "error")
    if utils.choose(["yes", "no"], "Install it now?") != "yes":
        utils.pause()
        return False
    subprocess.run(["sudo", "apt", "update"], capture_output=True, text=True)
    subprocess.run(["sudo", "apt", "install", "-y", "quota"])
    if not utils.is_pkg_installed("quota"):
        utils.log("Installation failed.", "error")
        utils.pause()
        return False
    utils.log("quota installed.", "success")
    return True


def quotas_menu():
    if not _ensure_quota_installed():
        return
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name("Disk Quotas")
        options = [
            "Show quota usage",  # 0
            "Set user quota",    # 1
            "Enable quotas",     # 2
            "Disable quotas",    # 3
            "",                  # 4
            "Back",              # 5
        ]
        choice = utils.show_menu(utils.create_menu(options, last))
        if choice == 0:
            show_quota_usage()
        elif choice == 1:
            set_user_quota()
        elif choice == 2:
            enable_quotas()
        elif choice == 3:
            disable_quotas()
        elif choice == 5 or choice is None:
            return
        last = choice
