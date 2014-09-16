#!/bin/bash

if [[ -z "$1" ]]; then
    echo "NO <ENV_NAME>"
    exit 1
fi

env_name="$1"
rm -f ${env_name}".tar.*"
mypath=~/
#Path where configuration xmls of VMs whill be saves
node_path=~/node_xml_save
xnode_path=node_xml_save
#Path where configuration xmls of networks will be saved
net_path=~/network_xml_save/
xnet_path=network_xml_save/
#Path where configuration xmls of snapshots will be saved
snapshot_path=~/snapshot_xml_save/
xsnapshot_path=snapshot_xml_save/
#Path where saves will be saved
save_path=~/save/
xsave_path=save/
data_file=image_path
_index=$(date '+%Y-%m-%d-%H-%M')

GZ=`which pigz || which gzip`

function tmp_dir {
    mkdir -p ~/network_xml_save
    mkdir -p ~/node_xml_save
    mkdir -p ~/save
}

function vm_save_creation {
    echo 'VM snapshot creation'
    nodes=(`virsh list --all | awk '{print $2}' | sed  -n "/^$env_name/p"`)
    for i in ${nodes[@]} ; do
        virsh dumpxml ${i} > $node_path/node_snapshot_${i}.xml
        echo "${i} xml is  Ready"
        virsh save ${i} $save_path/${i}_${_index} --verbose
        virsh restore ${i} $save_path/${i}_${_index}
    done
}

function network_xml_save {
    echo 'Network .xmls save'
    nets=(`virsh net-list --all | awk '{print $1}' | sed  -n "/$env_name/p"`)
    for i in ${nets[@]} ; do
        virsh net-dumpxml ${i} > $net_path/net_snapshot_${i}.xml
        echo "${i} is Ready"
    done
}

function arch_creation {
    echo 'Creation of archive'
    list=($(ls -1 ~/node_xml_save | tail -f -n 1))
    vm_path_one=$(egrep -m 1 "source file" $node_path/$list | cut -d "'" -f 2 | xargs dirname)
    xvm_path_one=$(dirname `echo ${vm_path_one}`)
    image_path=$(basename `echo ${vm_path_one}`)
    echo ${vm_path_one} > $mypath/$data_file
    containers=(`ls -1 $vm_path_one | sed  -n "/^$env_name/p"`)
    echo 'Images number:'${#containers[*]}
    for i in ${containers[@]} ; do
        FLIST="$FLIST $vm_path_one/${i}"
    done
    tar cvf - $FLIST -C $mypath $xnet_path $xnode_path $xsnapshot_path $data_file $xsave_path | $GZ -1 - > $env_name.tar.gz
}

function clean_tmp_dir {
    echo "CLEANING"
    rm -rf $net_path # Cleaning dir "~/network_xml_save"
    rm -rf $node_path   # Cleaning dir "~/node_xml_save"
    rm -rf $save_path #Cleaning dir "~/save"
    rm -rf $mypath/$data_file #Cleaning file "~/img_path" 
}

clean_tmp_dir
tmp_dir
vm_save_creation
network_xml_save
arch_creation
restore_state
clean_tmp_dir
