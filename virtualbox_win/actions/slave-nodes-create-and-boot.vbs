'    Copyright 2013 Mirantis, Inc.
'
'    Licensed under the Apache License, Version 2.0 (the "License"); you may
'    not use this file except in compliance with the License. You may obtain
'    a copy of the License at
'
'         http://www.apache.org/licenses/LICENSE-2.0
'
'    Unless required by applicable law or agreed to in writing, software
'    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
'    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
'    License for the specific language governing permissions and limitations
'    under the License.

' This script creates slaves node for the product, launches its installation,
' and waits for its completion


' Create and start slave nodes
for idx = 1 to cluster_size-1
	name=vm_name_prefix + "slave-" & idx
	if is_vm_present(name) then
		delete_vm name
	end if
	vm_ram = vm_slave_memory_default
	on error resume next
		vm_ram = vm_slave_memory_mb(idx)
	On Error GoTo 0
	wscript.echo name & " " & host_nic_name(0) & " " & vm_slave_cpu_cores & " " & vm_ram & " " & vm_slave_first_disk_mb
	create_vm name, host_nic_name(0), vm_slave_cpu_cores, vm_ram, vm_slave_first_disk_mb

	' Add additional NICs to VM
	
	add_hostonly_adapter_to_vm name, 2, host_nic_name(1)
	add_hostonly_adapter_to_vm name, 3, host_nic_name(2)

	' Add additional disks to VM
	add_disk_to_vm name, 1, vm_slave_second_disk_mb
	add_disk_to_vm name, 2, vm_slave_third_disk_mb

	enable_network_boot_for_vm name 
	start_vm name
next




' Report success
wscript.echo "Slave nodes have been created. They will boot over PXE and get discovered by the master node."
wscript.echo "To access master node, please point your browser to:"
wscript.echo "	http://" + vm_master_ip + ":8000/"
