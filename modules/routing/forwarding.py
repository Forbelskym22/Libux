import subprocess
from modules import utils

SYSCTL_KEY = "net.ipv4.ip_forward"
SYSCTL_CONF = "/etc/sysctl.d/99-libux.conf"

def forwarding_enabled():
    result = subprocess.run(["sysctl", "-n", SYSCTL_KEY], capture_output=True, text=True)
    return result.stdout.strip() == "1"

def toggle_forwarding():
    enabled = forwarding_enabled()
    action = "Disable" if enabled else "Enable"
    if utils.choose(["yes", "no"], f"{action} IP forwarding?") != "yes":
        return

    new_val = "0" if enabled else "1"
    result = subprocess.run(["sudo", "sysctl", "-w", f"{SYSCTL_KEY}={new_val}"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to set IP forwarding.", "error")
        utils.pause()
        return

    _persist_forwarding(new_val)

    if enabled:
        utils.log("IP forwarding disabled.", "success")
    else:
        utils.log("IP forwarding enabled. This machine will now forward packets between interfaces.", "success")
    utils.pause()

def _persist_forwarding(val):
    content = f"{SYSCTL_KEY} = {val}\n"
    result = subprocess.run(["sudo", "cat", SYSCTL_CONF], capture_output=True, text=True)
    if result.returncode == 0:
        import re
        existing = result.stdout
        if re.search(rf"^{SYSCTL_KEY}\s*=", existing, re.MULTILINE):
            import re
            new_content = re.sub(
                rf"^{SYSCTL_KEY}\s*=\s*\S+",
                f"{SYSCTL_KEY} = {val}",
                existing, flags=re.MULTILINE
            )
        else:
            new_content = existing.rstrip() + f"\n{content}"
    else:
        new_content = content

    subprocess.run(
        ["sudo", "bash", "-c", f"cat > {SYSCTL_CONF}"],
        input=new_content, text=True, capture_output=True
    )
    utils.log(f"Persisted to {SYSCTL_CONF}.", "success")
