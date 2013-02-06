#!/bin/bash 

# This file contains the functions to connect to the product VM and see if it became operational

is_product_vm_operational() {
    ip=$1
    username=$2
    password=$3
    prompt=$4

    # Log in into the VM, see if Puppet has completed its run
    # Looks a bit ugly, but 'end of expect' has to be in the very beginning of the line 
    result=$(
        expect << ENDOFEXPECT
        spawn ssh -oConnectTimeout=5 -oStrictHostKeyChecking=no -oCheckHostIP=no -oUserKnownHostsFile=/dev/null $username@$ip
        expect "connect to host" exit
        expect "*?assword:*"
        send "$password\r"
        expect "$prompt"
        send "grep -o 'Finished catalog run' /var/log/puppet/bootstrap_admin_node.log\r"
        expect "$prompt"
ENDOFEXPECT
    )

    # When you are launching command in a sub-shell, there are issues with IFS (internal field separator)
    # and parsing output as a set of strings. So, we are saving original IFS, replacing it, iterating over lines,
    # and changing it back to normal
    #
    # http://blog.edwards-research.com/2010/01/quick-bash-trick-looping-through-output-lines/
    OIFS="${IFS}"
    NIFS=$'\n'
    IFS="${NIFS}"

    for line in $result; do
        IFS="${OIFS}"
        if [[ $line = Finished* ]]; then
            return 0;
        fi    
        IFS="${NIFS}"
    done

    return 1
}

wait_for_product_vm_to_install() {
    ip=$1
    username=$2
    password=$3
    prompt=$4

    echo "Waiting for product VM to install. Please do NOT abort the script..."

    # Loop until master node gets successfully installed
    while ! is_product_vm_operational $ip $username $password "$prompt"; do
        sleep 5
    done
}

