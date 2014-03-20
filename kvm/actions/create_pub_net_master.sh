#!/bin/bash

iface=eth1.324
source config.sh

bring_up_public_access() {
    ip=$vm_master_ip
    username=$vm_master_username
    password=$vm_master_password
    prompt=$vm_master_prompt


#copy net iface config
        result=$(
        expect << ENDOFEXPECT1
        spawn scp -oConnectTimeout=2 -oStrictHostKeyChecking=no -oCheckHostIP=no ifcfg-${iface} ${username}@${ip}:/etc/sysconfig/network-scripts/ifcfg-${iface}
        expect "*?assword:*"
        send "$password\r"
        expect eof
ENDOFEXPECT1
)
        echo ""
    # Log in into the VM, see if Puppet has completed its run
    # Looks a bit ugly, but 'end of expect' has to be in the very beginning of the line
        result=$(
        expect << ENDOFEXPECT
        spawn ssh -oConnectTimeout=2 -oStrictHostKeyChecking=no -oCheckHostIP=no ${username}@${ip}
        expect "*?assword:*"
        send "$password\r"
        expect "*?${prompt}*"
        send "sed -ie 's/^GATEWAY=/#GATEWAY=/' /etc/sysconfig/network\r"
        expect "*?${prompt}*"
        send "ip ro del default\r"
        expect "*?${prompt}*"
        send "ifup ${iface}\r"
        expect "*?${prompt}*"
ENDOFEXPECT
    )

}
ssh-keygen -R $vm_master_ip
bring_up_public_access
