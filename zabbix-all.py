#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import subprocess
import os

# Змінні для налаштування
server_ip = "65.108.196.236"
hostname = os.getenv('HOST_NAME')

# Zabbix API налаштування
zabbix_url = "https://nodes.website/api_jsonrpc.php"
zabbix_user = "api_user"
zabbix_pass = "eZ57E5x55VAyZks"

def remove_old_zabbix():
    if b'zabbix-agent' in subprocess.check_output(['systemctl', 'list-units', '--full', '--all']):
        subprocess.run(['systemctl', 'stop', 'zabbix-agent'])
        subprocess.run(['apt', 'remove', '-y', 'zabbix-agent'])
    if os.path.exists("/etc/zabbix/"):
        subprocess.run(['rm', '-rf', '/etc/zabbix/'])

def install_zabbix():
    if not os.path.isfile("/etc/zabbix/zabbix_agentd.conf"):
        subprocess.run(['apt', 'remove', '--purge', 'zabbix-agent', '-y'])
        subprocess.run(['wget', 'https://repo.zabbix.com/zabbix/6.4/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.4-1+ubuntu20.04_all.deb'])
        subprocess.run(['dpkg', '-i', 'zabbix-release_6.4-1+ubuntu20.04_all.deb'])
        subprocess.run(['apt-get', 'update'])
        subprocess.run(['apt-get', 'install', '-y', 'zabbix-agent'])
        subprocess.run(['systemctl', 'restart', 'zabbix-agent'])
        subprocess.run(['systemctl', 'enable', 'zabbix-agent'])
        subprocess.run(['rm', '-f', 'zabbix-release_6.4-1+ubuntu20.04_all.deb'])

def config_zabbix():
    subprocess.run(['sed', '-i', f's/Hostname=.*/Hostname={hostname}/g', '/etc/zabbix/zabbix_agentd.conf'])
    subprocess.run(['sed', '-i', f's/Server=.*/Server={server_ip}/g', '/etc/zabbix/zabbix_agentd.conf'])
    subprocess.run(['sed', '-i', f's/ServerActive=.*/ServerActive={server_ip}/g', '/etc/zabbix/zabbix_agentd.conf'])
    subprocess.run(['sed', '-i', 's/# HostMetadata=/HostMetadata=autoreg.linux/', '/etc/zabbix/zabbix_agentd.conf'])
    subprocess.run(['systemctl', 'restart', 'zabbix-agent'])

# Отримання авторизаційного токена
def obtain_auth_token():
    auth_request = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": zabbix_user,
            "password": zabbix_pass
        },
        "id": 1
    }
    response = requests.post(zabbix_url, headers={'Content-Type': 'application/json'}, json=auth_request)
    return response.json()['result']

# Функція для отримання ID групи за її іменем
def get_group_id(group_name, auth_token):
    group_request = {
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "params": {
            "filter": {
                "name": [group_name]
            }
        },
        "auth": auth_token,
        "id": 1
    }
    response = requests.post(zabbix_url, headers={'Content-Type': 'application/json'}, json=group_request)
    return response.json()['result'][0]['groupid'] if response.json()['result'] else None

# Функція для створення групи
def create_group(group_name, auth_token):
    create_group_request = {
        "jsonrpc": "2.0",
        "method": "hostgroup.create",
        "params": {
            "name": group_name
        },
        "auth": auth_token,
        "id": 1
    }
    response = requests.post(zabbix_url, headers={'Content-Type': 'application/json'}, json=create_group_request)
    return response.json()['result']['groupids'][0]

# Функція для переміщення хоста до групи
def move_host_to_group(hostname, new_group_id, auth_token):
    host_request = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "filter": {
                "host": [hostname]
            }
        },
        "auth": auth_token,
        "id": 1
    }
    response = requests.post(zabbix_url, headers={'Content-Type': 'application/json'}, json=host_request)
    try:
        host_id = response.json()['result'][0]['hostid']
    except (KeyError, IndexError):
        print(f"Error: Host '{hostname}' not found.")
        return

    move_request = {
        "jsonrpc": "2.0",
        "method": "host.update",
        "params": {
            "hostid": host_id,
            "groups": [
                {"groupid": new_group_id}
            ]
        },
        "auth": auth_token,
        "id": 1
    }
    response = requests.post(zabbix_url, headers={'Content-Type': 'application/json'}, json=move_request)
    if response.json().get('error'):
        print(f"Error moving host '{hostname}' to group ID '{new_group_id}': {response.json()['error']['data']}")
    else:
        print(f"Host '{hostname}' moved successfully to group ID '{new_group_id}'.")

if __name__ == "__main__":
    remove_old_zabbix()
    install_zabbix()
    config_zabbix()
    
    auth_token = obtain_auth_token()

    if auth_token:
        # Після автореєстрації розподілимо хост по групах
        group_suffix = hostname.split('.')[-1]
        group_name = group_suffix
        group_id = get_group_id(group_name, auth_token)

        if not group_id:
            group_id = create_group(group_name, auth_token)

        if group_id:
            move_host_to_group(hostname, group_id, auth_token)
        else:
            print(f"Failed to create or retrieve group '{group_name}'")
    else:
        print("Failed to obtain authentication token.")
