# Libux
A text-based interface application designed for basic configuration of a Linux server, specifically the Debian distribution.

## Features
- [x] Firewall (iptables)
- [x] Network connectivity
- [x] DHCP
- [x] SSH
- [x] Apache2
- [x] Routing
- [x] Users and groups
- [x] Disk quotas
- [x] Permissions
- [x] MariaDB
- [x] Package manager (install / remove supported services)
- [x] PM2 process manager

> Implemented in v0.1.0: Firewall (iptables)  
> Implemented in v0.2.0: Network connectivity  
> Implemented in v0.3.0: DHCP  
> Implemented in v0.4.0: SSH  
> Implemented in v0.5.0: Apache2  
> Implemented in v0.6.0: Routing  
> Implemented in v0.7.0: Users and groups  
> Implemented in v0.8.0: Disk quotas & Permissions  
> Implemented in v0.9.0: MariaDB (install + phpMyAdmin)  
> Implemented in v1.0.0: Package manager + hardening & bug fixes  
> Implemented in v1.1.0: PM2 process manager  


## Requirements
- Python 3.x
- Debian
- Root permissions

## Installation
```
curl -LOJ https://libux.forbelsky.net
chmod +x ./libux
sudo ./libux
```

> Root permissions are required.

## License
MIT
