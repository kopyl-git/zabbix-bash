#!/usr/bin/env bash

# Змінні для налаштування
server_ip="65.108.196.236"
hostname="$HOST_NAME"

# Zabbix API налаштування
zabbix_url="https://nodes.website/api_jsonrpc.php"
zabbix_user="api_user"
zabbix_pass="eZ57E5x55VAyZks"
discovery_group_id="5"

remove_old_zabbix(){
    if [[ $(systemctl list-units --full -all | grep "zabbix-agent" | wc -l) -ne 0 ]]; then
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
        wget https://repo.zabbix.com/zabbix/6.4/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.4-1+ubuntu22.04_all.deb
        dpkg -i "zabbix-release_6.4-1+ubuntu22.04_all.deb"
        apt-get update
        apt-get install -y zabbix-agent
        systemctl restart zabbix-agent
        systemctl enable zabbix-agent
        rm -f "zabbix-release_6.4-1+ubuntu22.04_all.deb"
    fi
}

config_zabbix(){
    sed -i "s/Hostname=.*/Hostname=$hostname/g" /etc/zabbix/zabbix_agentd.conf
    sed -i "s/Server=.*/Server=$server_ip/g" /etc/zabbix/zabbix_agentd.conf
    sed -i "s/ServerActive=.*/ServerActive=$server_ip/g" /etc/zabbix/zabbix_agentd.conf
    sed -i "s/# HostMetadata=/HostMetadata=alt.autoreg/" /etc/zabbix/zabbix_agentd.conf
    systemctl restart zabbix-agent
}

# Отримання авторизаційного токена
auth_token=$(curl -s -X POST -H 'Content-Type: application/json' -d '{
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {
        "user": "'$zabbix_user'",
        "password": "'$zabbix_pass'"
    },
    "id": 1
}' $zabbix_url | jq -r '.result')

# Діагностичне виведення для перевірки відповіді
echo "Auth Response: $auth_response"

auth_token=$(echo $auth_response | jq -r '.result')

# Перевірка чи отримано токен
if [ "$auth_token" == "null" ] || [ -z "$auth_token" ]; then
    echo "Помилка: не вдалося отримати авторизаційний токен."
    exit 1
fi

# Функція для отримання ID групи по її імені
get_group_id() {
    local group_name=$1
    local group_id=$(curl -s -X POST -H 'Content-Type: application/json' -d '{
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "params": {
            "filter": {
                "name": [
                    "'$group_name'"
                ]
            }
        },
        "auth": "'$auth_token'",
        "id": 1
    }' $zabbix_url | jq -r '.result[0].groupid')
    echo $group_id
}

# Функція для створення групи
create_group() {
    local group_name=$1
    local group_id=$(curl -s -X POST -H 'Content-Type: application/json' -d '{
        "jsonrpc": "2.0",
        "method": "hostgroup.create",
        "params": {
            "name": "'$group_name'"
        },
        "auth": "'$auth_token'",
        "id": 1
    }' $zabbix_url | jq -r '.result.groupids[0]')
    echo $group_id
}

# Функція для переміщення хоста до групи
move_host_to_group() {
    local hostname=$1
    local new_group_id=$2
    local host_id=$(curl -s -X POST -H 'Content-Type: application/json' -d '{
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "filter": {
                "host": [
                    "'$hostname'"
                ]
            }
        },
        "auth": "'$auth_token'",
        "id": 1
    }' $zabbix_url | jq -r '.result[0].hostid')
    curl -s -X POST -H 'Content-Type: application/json' -d '{
        "jsonrpc": "2.0",
        "method": "host.update",
        "params": {
            "hostid": "'$host_id'",
            "groups": [
                {
                    "groupid": "'$new_group_id'"
                }
            ]
        },
        "auth": "'$auth_token'",
        "id": 1
    }' $zabbix_url > /dev/null
    
    # Діагностичне виведення для перевірки відповіді
    echo "Get Host Response: $response"

    local host_id=$(echo $response | jq -r '.result[0].hostid')

    response=$(curl -s -X POST -H 'Content-Type: application/json' -d '{
        "jsonrpc": "2.0",
        "method": "host.update",
        "params": {
            "hostid": "'$host_id'",
            "groups": [
                {
                    "groupid": "'$new_group_id'"
                }
            ]
        },
        "auth": "'$auth_token'",
        "id": 1
    }' $zabbix_url)

    # Діагностичне виведення для перевірки відповіді
    echo "Move Host Response: $response"
}

# Основний процес
remove_old_zabbix
install_zabbix
config_zabbix

# Зачекаємо деякий час для завершення автореєстрації
sleep 30

# Після автореєстрації розподілимо хост по групах
group_suffix=$(echo $hostname | awk -F '.' '{print $NF}')
group_name="Group $group_suffix"
group_id=$(get_group_id "$group_name")

if [ -z "$group_id" ]; then
    group_id=$(create_group "$group_name")
fi

move_host_to_group "$hostname" "$group_id"
