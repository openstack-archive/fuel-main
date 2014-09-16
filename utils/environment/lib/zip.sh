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
GZ=`which pigz || which gzip`

function tmp_dir {
mkdir -p ~/network_xml_save
mkdir -p ~/node_xml_save
mkdir -p ~/snapshot_xml_save
}

function vm_snapshot_creation {
echo 'VM snapshot creation'
nodes=(`virsh list --all | awk '{print $2}' | sed  -n "/^$env_name/p"`) 
echo ${#nodes[*]}
for i in ${nodes[@]} ; do
    virsh snapshot-create-as ${i} ${i}_$(date '+%Y-%m-%d-%H-%M')
    echo "${i} snapshot is  Ready"
    virsh dumpxml ${i} > $node_path/node_snapshot_${i}.xml
    echo "${i} xml is  Ready"
    snapshots=(`virsh snapshot-list ${i} | tail -f | awk '{print $1}'| sed  -n "/^$env_name/p"`)
    virsh snapshot-dumpxml ${i} $snapshots > $snapshot_path/$snapshots.xml    
done
}

function network_xml_save {
echo 'Network .xmls save' 
nets=(`virsh net-list --all | awk '{print $1}' | sed  -n "/$env_name/p"`)
echo ${#nets[*]}
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
containers=(`ls -1 $vm_path_one | sed  -n "/^$env_name/p"`)
current_user=(`whoami`)
owner_user=(`ls -lah $vm_path_one/$containers | awk '{print $3}'`)
echo $owner_user
echo $current_user
if [[ $current_user == $owner_user ]] || [[ -r "$vm_path_one/$containers" ]]; then
       echo "Permissions on $vm_path_one is ok"
   else
       echo "Insufficient permissions on files in the directory $vm_path_one" && exit 1
fi
echo 'Images number:'${#containers[*]}
for i in ${containers[@]} ; do
    FLIST="$FLIST $image_path/${i}"
done
nodes=(`virsh list --all | awk '{print $2}' | sed  -n "/^$env_name/p"`)
for i in ${nodes[@]} ; do
        virsh suspend ${i}
done
tar cvf - -C $mypath $xnet_path $xnode_path $xsnapshot_path -C $xvm_path_one/ $FLIST | $GZ -1 - > $env_name.tar.gz
for i in ${nodes[@]} ; do
        virsh resume ${i}
done
}

function clean_tmp_dir {
echo "-=CLEANING=-"
rm -rf $net_path # Cleaning dir "~/network_xml_save"
rm -rf $node_path   # Cleaning dir "~/node_xml_save"
rm -rf $snapshot_path #Cleaning dir "~/snapshot_xml_save"
}

clean_tmp_dir
tmp_dir
vm_snapshot_creation
network_xml_save
arch_creation
clean_tmp_dir
