#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import subprocess
import os

# Змінні для налаштування
server_ip = "65.108.196.236"
hostname = os.getenv('HOST_NAME')


def remove_old_zabbix():
    if b'zabbix-agent' in subprocess.check_output(['systemctl', 'list-units', '--full', '--all']):
        subprocess.run(['systemctl', 'stop', 'zabbix-agent'])
        subprocess.run(['apt', 'remove', '-y', 'zabbix-agent'])
    if os.path.exists("/etc/zabbix/"):
        subprocess.run(['rm', '-rf', '/etc/zabbix/'])

def install_zabbix():
    if not os.path.isfile("/etc/zabbix/zabbix_agentd.conf"):
        subprocess.run(['apt', 'remove', '--purge', 'zabbix-agent', '-y'])
        subprocess.run(['wget', 'https://repo.zabbix.com/zabbix/6.4/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.4-1+ubuntu22.04_all.deb'])
        subprocess.run(['dpkg', '-i', 'zabbix-release_6.4-1+ubuntu22.04_all.deb'])
        subprocess.run(['apt-get', 'update'])
        subprocess.run(['apt-get', 'install', '-y', 'zabbix-agent'])
        subprocess.run(['systemctl', 'restart', 'zabbix-agent'])
        subprocess.run(['systemctl', 'enable', 'zabbix-agent'])
        subprocess.run(['rm', '-f', 'zabbix-release_6.4-1+ubuntu22.04_all.deb'])

def config_zabbix():
    subprocess.run(['sed', '-i', f's/Hostname=.*/Hostname={hostname}/g', '/etc/zabbix/zabbix_agentd.conf'])
    subprocess.run(['sed', '-i', f's/Server=.*/Server={server_ip}/g', '/etc/zabbix/zabbix_agentd.conf'])
    subprocess.run(['sed', '-i', f's/ServerActive=.*/ServerActive={server_ip}/g', '/etc/zabbix/zabbix_agentd.conf'])
    subprocess.run(['sed', '-i', 's/# HostMetadata=/HostMetadata=autoreg.linux/', '/etc/zabbix/zabbix_agentd.conf'])
    subprocess.run(['systemctl', 'restart', 'zabbix-agent'])

if __name__ == "__main__":
    remove_old_zabbix()
    install_zabbix()
    config_zabbix()
