#!/usr/bin/env bash
hostname="$HOST_NAME"
groupname="25"
agent_ip="$(curl -s ifconfig.me)"
server_ip="65.108.196.236"
version="6.4"
zabbix_server_url="https://nodes.website/api_jsonrpc.php"
api_user="api_user"
api_user_pass="y0#rZjb.RnQgsLw"


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
    sed -i "s/ServerActive=.*/ServerActive=$server_ip/g" /etc/zabbix/zabbix_agentd.conf
    systemctl restart zabbix-agent
}


remove_from_zabbix_server(){
    host_id="$1"
    remove_host_data=$(wget -qO- https://raw.githubusercontent.com/Skurat/zabbix_scripts/main/zabbix_delete_host.json  | sed "s/\$host_id/$host_id/")

    # Request for remove host from zabbix server
    curl -s --request POST \
    --url "$zabbix_server_url" \
    --header "Authorization: Bearer ${AUTHORIZATION_TOKEN}" \
    --header 'Content-Type: application/json-rpc' \
    --data "$remove_host_data"

}
check_if_host_exist(){
    get_host_data=$(wget -qO- https://raw.githubusercontent.com/Skurat/zabbix_scripts/main/zabbix_check_if_host_exist.json  | sed "s/\$agent_ip/$agent_ip/")

    exist=$(curl -s --request POST \
    --url "$zabbix_server_url" \
    --header "Authorization: Bearer ${AUTHORIZATION_TOKEN}" \
    --header 'Content-Type: application/json-rpc' \
    --data "$get_host_data")
    host_id=( $(echo "$exist" | grep -o -E 'hostid":"[0-9]{4,}"' | grep -E -o '[0-9]+') )
    if [[ $(echo $exist | grep "hostid") ]]; then
        for host in "${host_id[@]}"; do
            remove_from_zabbix_server $host
            echo "Host with ID - $host already exist, it will be remove from zabbix server"
        done
    fi
}
add_agent_to_server(){
    data_auth=$(wget -qO- https://raw.githubusercontent.com/Skurat/zabbix_scripts/main/zabbix_authorization.json  | sed "s/\$api_user/$api_user/" | sed "s/\$api_user_pass/$api_user_pass/")

    AUTHORIZATION_TOKEN=$(curl -s --request POST \
    --url "$zabbix_server_url" \
    --header 'Content-Type: application/json-rpc' \
    --data $data_auth | cut -d',' -f2 | cut -d':' -f2 | sed -r 's/"//g')

    if [[ "$(echo $AUTHORIZATION_TOKEN | grep 'Invalid params')" ]]; then
        echo "! ! ! Invalid username or password"
        exit 0
    else
        echo "! ! ! Credentials is valid"
    fi

    # Check if host exist
    check_if_host_exist

    data_create_host=$(wget -qO- https://raw.githubusercontent.com/Skurat/zabbix_scripts/main/zabbix_create_host.json  | sed "s/\$hostname/$hostname/" | sed "s/\$agent_ip/$agent_ip/")
    # Request for add host
    curl --request POST \
    --url "$zabbix_server_url" \
    --header "Authorization: Bearer ${AUTHORIZATION_TOKEN}" \
    --header 'Content-Type: application/json-rpc' \
    --data $data_create_host
}

 remove_old_zabbix
 install_zabbix
 config_zabbix
add_agent_to_server
