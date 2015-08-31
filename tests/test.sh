#!/usr/bin/env bats
@test "When no parameters to ks script" {
  [ -z ${admin_interface+x} ];
  result=$(yes  `bash ./drives.sh`|awk '{print $1;}' | bash ../iso/ks.template 2>&1 |grep "DEVICE")
  echo $result
  [ "$result" = "+ echo DEVICE=eth0" ]
  result=$(bash ../iso/bootstrap_admin_node.docker.sh 2>&1|grep '\-\-iface=')
  echo $result
  [ "$result" = "+ fuelmenu --save-only --iface=eth0" ]
}

@test "When parameter admin_interface=eth3 to ks script" {
  [ -z ${admin_interface+x} ];
  result=$(yes  `bash ./drives.sh`|awk '{print $1;}' | admin_interface=eth3 bash ../iso/ks.template 2>&1 |grep "DEVICE")
  [ -z ${admin_interface+x} ];
  echo $result
  [ "$result" = "+ echo DEVICE=eth3" ]
  result=$(bash ../iso/bootstrap_admin_node.docker.sh 2>&1|grep '\-\-iface=')
  echo $result
  [ "$result" = "+ fuelmenu --save-only --iface=eth3" ]
}

