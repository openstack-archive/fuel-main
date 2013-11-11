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

' This script creates host-only interfaces for Fuel Web
' it does nothing if interface exists already


for idx = 0 to 2
	if not surely_create_hostonly_interface(host_nic_name(idx), host_nic_ip(idx), host_nic_mask(idx)) then
		wscript.echo "Creation of " & host_nic_name(idx) & " failed several times. "
		wscript.echo "This may be due to " & host_nic_ip(idx) & " assigned to other interface or its incorrect IP."
		wscript.echo "Please check interfaces and edit config.vbs."
		wscript.Quit 1
	end if
	' create_hostonly_interface host_nic_name(idx), host_nic_ip(idx), host_nic_mask(idx)
	wscript.echo "'" & host_nic_name(idx) & "' created"
	'wscript.echo "config.vbs, host_nic_name\(" & idx & "\)\s*=\s*.+$ , host_nic_name(" & idx & ")=""" & host_nic_name(idx) & """"
	Find_And_Replace "config.vbs", "host_nic_name\(" & idx & "\)\s*=\s*.+$", "host_nic_name(" & idx & ")=""" & host_nic_name(idx) & """"
next

' Sometimes VBoxManage can't properly configure IP at hostonlyif. 
' Have to log all interfaces to provide user propper information.
wscript.echo call_VBoxManage("list hostonlyifs")(1)