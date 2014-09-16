#!/bin/bash

if [[ -z "$1" || "$1" = *.tar.gz ]]; then
    echo "USAGE: ./environment.sh zip/unzip ENV_NAME"
    exit 1
fi

env_name="$1"
#Path where configuration xmls of VMs whill be saves
node_path=~/environment/node_xml_save
#Path where configuration xmls of networks will be saved
net_path=~/environment/network_xml_save
#Path where configuration xmls of snapshots will be saved
snapshot_path=~/environment/snapshot_xml_save
#Path where images of VMs whill be saves
img_path=~/environment/images

echo 'Unzip archive'
env_path=~/environment
mkdir -p $env_path
tar -xvzf ${env_name}.tar.gz -C $env_path

function check_free_nets {
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

function change_source_node_file {
    node_list=($(ls -1 $node_path))
    snapshot_list=($(ls -1 $snapshot_path))
    vm_path=$(egrep -m 1 "source file" $node_path/$node_list | cut -d "'" -f 2 | xargs dirname)
    vm_path=$(echo $vm_path | sed -e 's:/:\\/:g')
    vm_snapshot_path=$(egrep -m 1 "source file" $snapshot_path/$snapshot_list | cut -d "'" -f 2 | xargs dirname)
    vm_snapshot_path=$(echo $vm_snapshot_path | sed -e 's:/:\\/:g')
    img_path_mod=$(echo $(/bin/ls -d $img_path) | sed -e 's:/:\\/:g')
    for k in ${node_list[@]}; do
        sed -i -e 's/'$vm_path'/'$img_path_mod'/g' $node_path/${k}
    done
    for k in ${snapshot_list[@]}; do
        sed -i -e 's/'$vm_snapshot_path'/'$img_path_mod'/g' $snapshot_path/${k}
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

function define_snapshots {
    echo 'Define snapshots'
    node_start=(`virsh list --all | awk '{print $2}' | sed  -n "/^$env_name/p"`)
    snapshot_list=(`ls -1 $snapshot_path`)
    for i in ${node_start[@]} ; do
        virsh snapshot-create ${i} $snapshot_path/$i*xml
    done
}

function reverting_snapshot {
    echo 'Reverting snapshot'
    for i in ${node_start[@]};do
        snapshot_list_name=(`virsh snapshot-list ${i} | tail -f -n +3 |awk '{print $1}' | sed  -n "/^$env_name/p"`)
        virsh snapshot-revert ${i} $snapshot_list_name
        echo "Ready ${i}"
    done
}

function clean_tmp_dir {
    echo "-=CLEANING=-"
    rm -rf $net_path
    rm -rf $node_path
    rm -rf $snapshot_path
}

check_free_nets
define_net
change_source_node_file
define_vm
start_machines
define_snapshots
reverting_snapshot
clean_tmp_dir
