#!/bin/bash

ssh_options='-oConnectTimeout=5 -oStrictHostKeyChecking=no -oCheckHostIP=no -oUserKnownHostsFile=/dev/null -oRSAAuthentication=no -oPubkeyAuthentication=no'

#ip='10.20.0.2'
#username='root'
#password='r00tme'
#prompt='*?]#'

ip=$1
username=$2
password=$3
prompt=$4
container_name=$5

greenc='\033[0;32m'
NORMAL='\033[0m'
redc='\e[0;31m'

container_test(){
echo -e "${NORMAL}Testing $container_name docker container..."
container_status=$(   expect << ENDOFEXPECT
        spawn ssh $ssh_options $username@$ip
        expect "connect to host" exit
        expect "*?assword:*"
        send "$password\r"
        expect "$prompt"
	send "cp /usr/bin/dockerctl /usr/bin/dockerctl-test\r"
	expect "$prompt"
        send "/usr/bin/dockerctl-test check $container_name\r"
        expect "$prompt"
ENDOFEXPECT
)

    OIFS="${IFS}"
    NIFS=$'\n'
    IFS="${NIFS}"

    for line in $container_status; do
        IFS="${OIFS}"
        if [[ $line == *ready* ]]; then
	    IFS="${NIFS}"
	    echo -e "${NORMAL}$container_name container is ready - ${greenc}[OK]${NORMAL}"
        return 0;
        fi
        IFS="${NIFS}"
    done

    echo -e "${redc}Container \"$container_name\" is not ready yet.${NORMAL}\n"

    return 1
}

    count=0
    while [ $count -ne 7 ]
	do
	(( count++ ))
	if container_test; then
            break
        fi
	sleep 1
    done


remove_test_script=$(   expect << ENDOFEXPECT_1
        spawn ssh $ssh_options $username@$ip
        expect "connect to host" exit
        expect "*?assword:*"
        send "$password\r"
        expect "$prompt"
	send "rm -f -r /usr/bin/dockerctl-test\r"
	expect "$prompt"
ENDOFEXPECT_1
)
