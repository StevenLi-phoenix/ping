#!/bin/bash

ZIPNAME='cr05'

# update packages
apt update
apt upgrade -y
apt install unzip
apt autoremove


# create swap
cd /
fallocate -l 1G /swapfile
dd if=/dev/zero of=/swapfile bs=4096 count=1048576
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo "/swapfile swap swap defaults 0 0" >> /etc/fstab
swapon --show
free -h
sysctl vm.swappiness=5
echo "vm.swappiness=5" >> /etc/sysctl.conf

# download and unzip files
cd
wget http://47.95.223.74:8000/files/$ZIPNAME
unzip -o $ZIPNAME

# create daemon
echo "[Unit]
Description=A daemon for ping worker.

[Service]
Type=simple
User=root
WorkingDirectory=/root/ping
ExecStart=python3 /root/ping/main.py
Restart=always

[Install]
WantedBy=multi-user.target"  > /etc/systemd/system/ping.service

# systemctl reload
systemctl daemon-reload
systemctl enable ping
systemctl start ping
