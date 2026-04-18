import os
import subprocess
from modules import utils
from .site_helpers import read_conf, write_conf
import re

def htpasswd_path(name):
    return f"/etc/apache2/.htpasswd_{name}"

def auth_enabled(site_conf):
    return "AuthType Basic" in read_conf(site_conf)

def enable_auth(site_conf, realm, htpasswd):
    auth_block = (
        f"\n    <Location />\n"
        f"        AuthType Basic\n"
        f"        AuthName \"{realm}\"\n"
        f"        AuthUserFile {htpasswd}\n"
        f"        Require valid-user\n"
        f"    </Location>\n"
    )
    content = read_conf(site_conf)
    write_conf(site_conf, content.replace("</VirtualHost>", auth_block + "</VirtualHost>"))

def disable_auth(site_conf):
    content = read_conf(site_conf)
    write_conf(site_conf, re.sub(
        r"\s*<Location\s*/\s*>.*?</Location>", "", content, flags=re.DOTALL
    ))

def manage_auth(name, site_conf):
    last = 0
    while True:
        os.system("clear")
        utils.print_menu_name(f"Auth - {name}")

        enabled = auth_enabled(site_conf)
        status_str = f"{utils.GREEN}enabled{utils.RESET}" if enabled else f"{utils.GRAY}disabled{utils.RESET}"
        print(f"  {utils.WHITE}Basic Auth: {status_str}\n{utils.RESET}")

        options = [
            "Disable auth" if enabled else "Enable auth",
            "Add user", "Remove user", "Show users", "", "Back"
        ]
        choice = utils.show_menu(utils.create_menu(options, last))

        if choice == 0:
            if enabled:
                if utils.choose(["yes", "no"], "Disable auth and remove htpasswd?", "error") == "yes":
                    disable_auth(site_conf)
                    subprocess.run(["sudo", "rm", "-f", htpasswd_path(name)], capture_output=True)
                    utils.log("Auth disabled. Reload Apache2 to apply.", "success")
                    utils.pause()
            else:
                subprocess.run(["sudo", "a2enmod", "auth_basic"], capture_output=True)
                realm = utils.ask("Message of the day (Enter for Restricted Area)")
                if realm is None:
                    continue
                if not realm:
                    realm = "Restricted Area"
                enable_auth(site_conf, realm, htpasswd_path(name))
                utils.log("Auth enabled. Add users and reload Apache2 to apply.", "success")
                utils.pause()

        elif choice == 1:
            username = utils.ask_required("Username")
            if username is None:
                continue
            hp = htpasswd_path(name)
            check = subprocess.run(["sudo", "test", "-f", hp], capture_output=True)
            cmd = ["sudo", "htpasswd"] + (["-c"] if check.returncode != 0 else []) + [hp, username]
            subprocess.run(cmd)
            utils.pause()

        elif choice == 2:
            hp = htpasswd_path(name)
            result = subprocess.run(["sudo", "cat", hp], capture_output=True, text=True)
            if result.returncode != 0 or not result.stdout.strip():
                utils.log("No users found.", "info")
                utils.pause()
                continue
            users = [l.split(":")[0] for l in result.stdout.strip().splitlines() if ":" in l]
            user = utils.choose(users, "Select user to remove")
            if user is None:
                continue
            subprocess.run(["sudo", "htpasswd", "-D", hp, user], capture_output=True)
            utils.log(f"User {user} removed.", "success")
            utils.pause()

        elif choice == 3:
            os.system("clear")
            utils.print_menu_name(f"Users - {name}")
            result = subprocess.run(["sudo", "cat", htpasswd_path(name)], capture_output=True, text=True)
            if result.returncode != 0 or not result.stdout.strip():
                utils.log("No users found.", "info")
            else:
                for line in result.stdout.strip().splitlines():
                    print(f"  {utils.YELLOW}{line.split(':')[0]}{utils.RESET}")
            utils.pause()

        elif choice == 5 or choice is None:
            return

        last = choice
