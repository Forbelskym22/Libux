import os
import subprocess
from modules import utils
from .shared import SITES_AVAILABLE
from .site_helpers import (
    parse_conf, read_conf, write_conf,
    enable_conf, disable_conf,
    ssl_vhost, redirect_vhost,
)

def generate_self_signed_cert(name):
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

def enable_ssl_module():
    return subprocess.run(["sudo", "a2enmod", "ssl"], capture_output=True).returncode == 0

def add_ssl_vhost(name, group):
    os.system("clear")
    utils.print_menu_name(f"Add HTTPS - {name}")

    enable_ssl_module()
    cert_path, key_path = generate_self_signed_cert(name)
    if not cert_path:
        utils.pause()
        return

    doc_root = f"/var/www/{name}"
    if group["http"]:
        info = parse_conf(group["http"])
        if info["doc_root"] != "-":
            doc_root = info["doc_root"]

    ssl_file = f"{name}-ssl.conf"
    subprocess.run(
        ["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{ssl_file}"],
        input=ssl_vhost(name, doc_root, cert_path, key_path),
        text=True, capture_output=True
    )
    enable_conf(ssl_file)
    utils.log(f"{ssl_file} created and enabled.", "success")

    if utils.choose(["yes", "no"], "Add HTTP->HTTPS redirect?") == "yes":
        if group["http"]:
            disable_conf(group["http"])
            subprocess.run(["sudo", "rm", f"{SITES_AVAILABLE}/{group['http']}"], capture_output=True)
            utils.log("HTTP vhost removed.", "success")
        info = parse_conf(ssl_file)
        server_name = info["server_name"] if info["server_name"] != "-" else name
        redirect_file = f"{name}-redirect.conf"
        subprocess.run(
            ["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{redirect_file}"],
            input=redirect_vhost(server_name), text=True, capture_output=True
        )
        enable_conf(redirect_file)
        utils.log("HTTP->HTTPS redirect created.", "success")

    utils.log("Reload Apache2 to apply.", "success")
    utils.pause()

def toggle_redirect(name, group):
    if group["redirect"]:
        if utils.choose(["yes", "no"], f"Remove redirect {group['redirect']}?", "error") != "yes":
            return
        disable_conf(group["redirect"])
        subprocess.run(["sudo", "rm", f"{SITES_AVAILABLE}/{group['redirect']}"], capture_output=True)
        utils.log("Redirect removed. Reload Apache2 to apply.", "success")
    else:
        if not group["ssl"]:
            utils.log("No SSL vhost found. Add HTTPS first.", "error")
            utils.pause()
            return
        info = parse_conf(group["ssl"])
        server_name = info["server_name"] if info["server_name"] != "-" else name
        redirect_file = f"{name}-redirect.conf"
        subprocess.run(
            ["sudo", "bash", "-c", f"cat > {SITES_AVAILABLE}/{redirect_file}"],
            input=redirect_vhost(server_name), text=True, capture_output=True
        )
        enable_conf(redirect_file)
        utils.log("Redirect created and enabled. Reload Apache2 to apply.", "success")
    utils.pause()
