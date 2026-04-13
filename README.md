# Libux
A text-based interface application designed for basic configuration of a Linux server, specifically the Debian distribution.

## Features
- [x] Firewall (iptables)
- [x] Network connectivity
- [x] DHCP
- [x] SSH
- [ ] Apache2
- [ ] Routing
- [ ] Users and groups
- [ ] Disk quotas
- [ ] Permissions
- [ ] MariaDB

> Implemented in v0.1.0: Firewall (iptables)  
> Implemented in v0.2.0: Network connectivity  
> Implemented in v0.3.0: DHCP
> Planned for future releases: SSH, Apache2, Routing, Users and groups, Disk quotas, Permissions, MariaDB


## Requirements
- Python 3.x
- Debian
- Root permissions

## Installation
```
git clone https://github.com/Forbelskym22/Libux.git
cd Libux
sudo ./install.sh
```

## Usage
```bash
sudo ./start.sh
```
> Root permissions are required.

## License
MIT