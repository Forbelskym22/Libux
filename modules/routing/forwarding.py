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
    if utils.choose(["yes", "no"], f"{action} Routing?") != "yes":
        return

    new_val = "0" if enabled else "1"
    result = subprocess.run(["sudo", "sysctl", "-w", f"{SYSCTL_KEY}={new_val}"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to set Routing.", "error")
        utils.pause()
        return

    _persist_forwarding(new_val)

    if enabled:
        utils.log("Routing disabled.", "success")
    else:
        utils.log("Routing enabled. This machine will now forward packets between interfaces.", "success")
    utils.pause()

def prompt_enable_forwarding():
    if forwarding_enabled():
        return
    utils.log("IP forwarding is currently disabled; FORWARD rules won't take effect until it's enabled.", "info")
    if utils.choose(["yes", "no"], "Enable IP forwarding now?") != "yes":
        return
    result = subprocess.run(["sudo", "sysctl", "-w", f"{SYSCTL_KEY}=1"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        utils.log(result.stderr.strip() or "Failed to enable Routing.", "error")
        return
    _persist_forwarding("1")
    utils.log("Routing enabled.", "success")


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
