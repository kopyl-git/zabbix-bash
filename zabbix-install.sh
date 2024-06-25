#!/usr/bin/env bash
hostname="$HOST_NAME"
server_ip="65.108.196.236"

remove_old_zabbix(){
    if [[ $(systemctl list-units --full -all | grep "zabbix-agent" | wc -l) ]]; then
        systemctl stop zabbix-agent
        apt remove -y zabbix-agent
    fi
    if [[ -d "/etc/zabbix/" ]]; then
        rm -rf /etc/zabbix/
    fi
}

install_zabbix(){
    if [[ ! -f "/etc/zabbix/zabbix_agentd.conf" ]]; then
        apt remove --purge zabbix-agent -y
        wget https://repo.zabbix.com/zabbix/6.4/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.4-1+ubuntu20.04_all.deb
        dpkg -i "zabbix-release_6.4-1+ubuntu20.04_all.deb"
        apt-get update
        apt-get install -y zabbix-agent
        systemctl restart zabbix-agent
        systemctl enable zabbix-agent
        rm -f "zabbix-release_6.4-1+ubuntu20.04_all.deb"
    fi
}

config_zabbix(){
    sed -i "s/Hostname=.*/Hostname=$hostname/g" /etc/zabbix/zabbix_agentd.conf
    sed -i "s/Server=.*/Server=$server_ip/g" /etc/zabbix/zabbix_agentd.conf
    sed -i "s/ServerActive=.*/ServerActive=$server_ip/g" /etc/zabbix/zabbix_agentd.conf
    sed -i "s/# HostMetadata=/HostMetadata=autoreg.linux/" /etc/zabbix/zabbix_agentd.conf
    systemctl restart zabbix-agent
}


remove_old_zabbix
install_zabbix
config_zabbix
