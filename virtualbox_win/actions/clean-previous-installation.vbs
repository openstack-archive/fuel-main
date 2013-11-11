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

' This script check that there is no previous installation of Fuel Web (if there is one, the script deletes it)


' Delete all VMs from the previous Fuel Web installation
delete_vms_multiple vm_name_prefix

' Delete all host-only interfaces
'delete_all_hostonly_interfaces

for idx = 0 to 2
	if is_hostonly_interface_present(host_nic_name(idx)) then
		delete_hostonly_interface(host_nic_name(idx))
	end if
next

' check for interfaces with IP addresses as in config.vbs
hostonly_interfaces_ips = get_vbox_value ("list hostonlyifs", "IPAddress")
for idx = 0 to 2
	if instr(hostonly_interfaces_ips,host_nic_ip(idx))>0 then
		wscript.echo "Fatal error. There is already host-only interface with IP address " + host_nic_ip(idx) 
		wscript.echo "Remove that interface or change value host_nic_ip(" & idx & ") in config.vbs."
		wscript.quit 1
	end If 
next

wscript.echo call_VBoxManage("list hostonlyifs")(1)