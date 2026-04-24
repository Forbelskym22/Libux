import os
import subprocess
from modules import utils
from .shared import is_pm2_installed, is_nodejs_installed


def install_pm2():
    os.system("clear")
    utils.print_menu_name("Install PM2")

    #check pm2
    if is_pm2_installed():
        utils.log("PM2 is already installed.", "info")
        utils.pause()
        return
    
    # check node
    if not is_nodejs_installed():
        utils.log("Node.js is not installed. Run: apt install nodejs npm", "error")
        pick = utils.choose(["yes", "no"], "Install node?")
        if pick != "yes":
            return
        utils.log("Installing Node.js and npm...", "info")
        subprocess.run(["apt-get", "install","-y", "nodejs","npm"])
        if not is_nodejs_installed():
            utils.log("Node installation failed.", "error")
            utils.pause()
            return
        utils.log("Node is installed.", "success")
            

    # instalace 
    utils.log("Installing PM2 via npm...", "info")
    subprocess.run(["npm", "install", "-g", "pm2"])

    #vyhodnoceni uspechu
    if is_pm2_installed():
        utils.log("PM2 installed.", "success")
    else:
        utils.log("PM2 installation failed.", "error")
    utils.pause()


def remove_pm2():
    os.system("clear")
    utils.print_menu_name("Remove PM2")
    if not is_pm2_installed():
        utils.log("PM2 is not installed.", "info")
        utils.pause()
        return
    if utils.choose(["yes","no"], "Remove PM2?", "error") != "yes":
        return
    subprocess.run(["npm","uninstall","-g","pm2"])
    if not is_pm2_installed():
        utils.log("PM2 removed.", "success")
    else:
        utils.log("Removal failed.", "error")
    utils.pause()