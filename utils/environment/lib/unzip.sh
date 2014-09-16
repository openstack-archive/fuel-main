#!/bin/bash

if [[ -z "$1" || "$1" = *.tar.gz ]]; then
    echo "USAGE: ./environment.sh zip/unzip ENV_NAME"
    exit 1
fi

env_name="$1"
env_path=${HOME}/relocated_env
mkdir -p $env_path/save_xml_only
#Path where configuration xmls of VMs whill be saves
node_path=$env_path/node_xml_save
#Path where configuration xmls of networks will be saved
net_path=$env_path/network_xml_save
#Path where configuration xmls of snapshots will be saved
snapshot_path=$env_path/snapshot_xml_save
#Path where RAM states are saved
save_path=$env_path/save
save_path_xml=$env_path/save_xml_only

echo 'Unzip archive'
tar -xvzf ${env_name}.tar.gz -C $env_path image_path
img_path="$(cat ${env_path}/image_path | sed -e 's:/::')"
tar -xvzf ${env_name}.tar.gz -C / $img_path
tar -xvzf ${env_name}.tar.gz -C $env_path node_xml_save network_xml_save save


function check_free_nets {
    echo 'Check Free Nets'
    net_list_snap=$(egrep "name" $net_path/* | cut -d ">" -f 2 | cut -d "<" -f 1 | sed  -e '/^$/d')
    net_list_host=$(virsh net-list --all | awk '{print $1}' | sed  -n "/^$env_name/p")
    for i in ${net_list_snap} ;do
        for j in ${net_list_host} ;do
            if [[ ${i} == ${j} ]]; then
                echo "Matching networks ${i}" && exit 1
            fi
        done
    done
    net_ip_host=`virsh net-list --all | tail -n +3| sed  -e 's/yes//g; s/active//g'`
    net_ip_snap=`ls -l $net_path | awk '{print $9}'| tail -n +3`
    for i in ${net_ip_host} ;do
        ip_list_host="$ip_list_host `virsh net-dumpxml ${i} | egrep -m 1 "ip address" | cut -d "'" -f 2`"
        for j in ${net_ip_snap} ;do
            ip_list_snap="$ip_list_snap `cat $net_path/${j} | egrep -m 1 "ip address" | cut -d "'" -f 2`"
            for q in ${ip_list_host} ;do
                for w in ${ip_list_snap} ;do
                    if [[ ${w} == ${q} ]]; then
                        echo "Matching virtual network gateway ips ${w}" && exit 1
                    fi
                done
            done
        done
    done
}

function define_net {
    echo 'Define NET'
    nets=(`ls -l $net_path | awk '{print $9}'`)
    for i in ${nets[@]} ; do
        virsh net-define $net_path/${i}
    done
    nets_start=(`virsh net-list --all | awk '{print $1}' | sed  -n "/$env_name/p"`)
    for i in ${nets_start[@]} ; do
        virsh net-start ${i}
        virsh net-autostart ${i}
    done
}

function define_vm {
    echo 'Define VM'
    nodes=(`ls -l $node_path | awk '{print $9}'`)
    for i in ${nodes[@]} ; do
        virsh define $node_path/${i}
    done
}

function start_machines {
    echo 'Start domains'
    node_start=(`virsh list --all | awk '{print $2}' | sed  -n "/^$env_name/p"`)
    for i in ${node_start[@]} ; do
        virsh start ${i}
    done
}

function restore {
    echo 'Restore VM'
    save_list=($(ls -1 $save_path))
    for k in ${save_list[@]}; do
        virsh restore $save_path/${k}
    done
}

function get_master_ip {
    echo "Get master ip"
    num=2
    adm_net=(`ls -1 $net_path | grep net_snapshot_${env_name}_admin.xml`)
    adm_gate=(`cat $net_path/$adm_net | egrep -m 1 "ip address" | cut -d "'" -f 2 | sed "s/.$//"`)
    master_ip=${adm_gate}$num
}

function ntpsync {
    echo "NTPSYNC"
    target="root@${master_ip}"
    password="r00tme"
    echo "id=(\`fuel node | awk '{print \$1}' | tail -n +3\`); for i in \${id[@]} ; do ssh node-\${i} \"ntpdate -u $master_ip\"; done" > $env_path/ntpsync.sh
    chmod +x $env_path/ntpsync.sh
    expect << ENDOFEXPECT
    spawn scp -r $env_path/ntpsync.sh ${target}:/root/
    expect "password:"
    send "$password\r"
    expect "# "
    spawn ssh ${target}
    expect "password:"
    send "$password\r"
    expect "# "
    send "sh /root/ntpsync.sh\r"
    expect "# "
    send "exit\r"
    expect eof
ENDOFEXPECT
}

function clean_tmp_dir {
    echo "CLEANING"
    rm -rf $net_path
    rm -rf $node_path
    rm -rf $save
    rm -f  $env_path/image_path
    rm -rf ~/relocated_env
}

check_free_nets
define_net
define_vm
restore
get_master_ip
ntpsync
clean_tmp_dir
