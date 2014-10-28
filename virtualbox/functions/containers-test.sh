#!/bin/bash

#    Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

#
# This file contains the functions for docker containers check on fuel master node
#

ssh_options='-oConnectTimeout=5 -oStrictHostKeyChecking=no -oCheckHostIP=no -oUserKnownHostsFile=/dev/null -oRSAAuthentication=no -oPubkeyAuthentication=no'

greenc='\033[0;32m'
NORMAL='\033[0m'
redc='\e[0;31m'

# create test script
create_test_script(){

ip=$1
username=$2
password=$3
prompt=$4

create_script=$(   expect << ENDOFEXPECT_1
        spawn ssh $ssh_options $username@$ip
        expect "connect to host" exit
        expect "*?assword:*"
        send "$password\r"
        expect "$prompt"
        send "cp /usr/bin/dockerctl /usr/bin/dockerctl-test\r"
        expect "$prompt"
ENDOFEXPECT_1
)
}



# Obtain the status of the container
container_test(){
echo -e "${NORMAL}Testing $container_name docker container..."
docker_container_status=$(   expect << ENDOFEXPECT
        spawn ssh $ssh_options $username@$ip
        expect "connect to host" exit
        expect "*?assword:*"
        send "$password\r"
        expect "$prompt"
        send "/usr/bin/dockerctl-test check $container_name\r"
        expect "$prompt"
ENDOFEXPECT
)

    OIFS="${IFS}"
    NIFS=$'\n'
    IFS="${NIFS}"

    for line in $docker_container_status; do
        IFS="${OIFS}"
        if [[ $line == *ready* ]]; then
        IFS="${NIFS}"
        echo -e \
        "${NORMAL}$container_name container is ready - ${greenc}[OK]${NORMAL}"
        return 0;
        fi
        IFS="${NIFS}"
    done
    yellow='\e[0;33m'
    echo -e "${yellow}Container $container_name is not ready yet."
    echo -e "${NORMAL}Repeat the test:"

    return 1
}

# Analyze the status of the container
container_status(){

ip=$1
username=$2
password=$3
prompt=$4
container_name=$5


    count=0
    while [ $count -ne 1 ]
    do
    (( count++ ))
       if container_test; then
            break
       fi
    done

    local res=$(container_test)
    echo "res" $res "res"
    if [[ $res == *not* ]]
      then
      echo "Container $container_name fails to start.";
      return 1
     else
    return 0
     fi
}

# Remove test script from fuel master node
remove_test_script(){

ip=$1
username=$2
password=$3
prompt=$4

remove_script=$(   expect << ENDOFEXPECT_1
        spawn ssh $ssh_options $username@$ip
        expect "connect to host" exit
        expect "*?assword:*"
        send "$password\r"
        expect "$prompt"
        send "rm -f -r /usr/bin/dockerctl-test\r"
        expect "$prompt"
ENDOFEXPECT_1
)
}

