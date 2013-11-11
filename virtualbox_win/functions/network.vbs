Option Explicit
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

' This file contains the functions to manage host-only interfaces in the system

function get_hostonly_interfaces() 
' Reads host-only interfaces names.
' Returns: string separated by CR LF.
	get_hostonly_interfaces = get_vbox_value ("list hostonlyifs", "Name")
	'echo -e `VBoxManage list hostonlyifs | grep '^Name' | sed 's/^Name\:[ \t]*//' | uniq` 
end function


function is_hostonly_interface_present(strIfName) 
' Check if interface is in list of host-only interfaces
' Returns: boolean
	dim lstIfs, arrIfs, i
	lstIfs = get_hostonly_interfaces()
	arrIfs = Split(lstIfs,vbcrlf)
	' Check that the list of interfaces contains the given interface
	is_hostonly_interface_present = false
	for i = 0 to Ubound(arrIfs)
		if arrIfs(i) = strIfName then
			is_hostonly_interface_present = True
			exit for 
		end if
	next
end function
'wscript.echo is_hostonly_interface_present("VirtualBox Host-Only Ethernet Adapter") 


function check_hostonly_interface(strIfName, strIp, strMask)
' Check if interface have given ip address and mask
' Returns: boolean 
	Dim listing, arrLines, linesNb, i
	listing = get_vbox_value ("list hostonlyifs", "(Name|IPAddress|NetworkMask)")
	arrLines = Split(listing,vbcrlf)
	linesNb = Ubound(arrLines) + 1
	if linesNb Mod 3 <> 0 then
		wscript.echo "Something went wrong..."
		exit function
	end if
	check_hostonly_interface = False
	for i = 0 to linesNb-1 step 2
		if arrLines(i) = strIfName then
			if arrLines(i+1) = strIp and arrLines(i+2) = strMask then
				check_hostonly_interface = True
			else
				check_hostonly_interface = False
			end if
			exit for
		end if
	next
end Function 
'wscript.echo check_hostonly_interface("VirtualBox Host-Only Ethernet Adapter", "192.168.56.1", "255.255.255.0")


function surely_create_hostonly_interface(byref strIfName, strIp, mask)
' Create hostonly interface and configure it with IP and mask.
' If created interface have different name value of strIfName variable changes.
' Sometimes VBoxManage can't properly configure IP at hostonly interface. 
' In case if IP and mask not configured properly interface deleted and recreated in loop.
' Returns: nothing
	dim i, max_tries, sleep_seconds
	max_tries = 5
	sleep_seconds = 5
	surely_create_hostonly_interface = False

	for i = 1 to max_tries
		if is_hostonly_interface_present(strIfName) then 
			delete_hostonly_interface strIfName
			WScript.sleep sleep_seconds * 1000
		end if

		create_hostonly_interface strIfName, strIp, mask

		if is_hostonly_interface_present(strIfName) then 
			if check_hostonly_interface (strIfName, strIp, mask) then
				surely_create_hostonly_interface = True
				exit for
			else
				wscript.echo "Interface was not created properly."
			end if
		end if

		WScript.sleep sleep_seconds * 1000
	next
end Function 
'wscript.echo surely_create_hostonly_interface ("VirtualBox Host-Only Ethernet Adapter #8", "192.168.1.1", "255.255.255.0")


function create_hostonly_interface(byref strIfName, strIp, strMask)
' Create hostonly interface and configure it with IP and mask
' If created interface have different name value of strIfName variable changes.
' Returns: nothing
	wscript.echo "Creating host-only interface (name ip netmask): " & strIfName  & " " & strIp & " " & strMask
	' Exit if the interface already exists (deleting it here is not safe, as VirtualBox creates hostonly adapters sequentially)
	if is_hostonly_interface_present (strIfName) then
		wscript.echo "Fatal error. Interface " + strIfName + " cannot be created because it already exists."
		exit Function
	end if

	dim ret, objRXP, objMatches
	Set objRXP = New RegExp : objRXP.Global = True : objRXP.Multiline = True
	objRXP.Pattern = "Interface '([^']+)' was successfully created"

	' Create the interface
	ret = call_VBoxManage ("hostonlyif create")
	set objMatches = objRXP.Execute(ret(1)) 
	if objMatches.count > 0 then
		strIfName = objMatches(0).SubMatches(0)
	end if

	' If it does not exist after creation, let's abort
	if not is_hostonly_interface_present (strIfName) then
		wscript.echo "Fatal error. Interface " + strIfName + " does not exist after creation."
		exit Function
	end if

	' Disable DHCP
	wscript.echo "Disabling DHCP server on interface: " + strIfName + "..."
	'VBoxManage dhcpserver remove --ifname $strIfName 2>/dev/null
	call_VBoxManage "dhcpserver remove --ifname """ + strIfName  + """"

	' Set up IP address and network mask
	wscript.echo "Configuring IP address " + strIp + " and network mask " + strMask + " on interface: " + strIfName + "..."
	call_VBoxManage "hostonlyif ipconfig """ + strIfName + """ --ip " + strIp + " --netmask " + strMask
end function


Function delete_hostonly_interface(strIfName)
' Delete given host-only interface
' Returns: nothing
		wscript.echo "Deleting host-only interface: " + strIfName + "..."
		call_VBoxManage "hostonlyif remove """ + strIfName + """"
end Function


function delete_all_hostonly_interfaces() 
' Delete all host-only interfaces
' Returns: nothing
	dim arrIfs, strIfName
	arrIfs = Split(get_hostonly_interfaces(), vbcrlf)

	' Delete every single hostonly interface in the system
	for each strIfName in arrIfs 
		delete_hostonly_interface(strIfName)
	next
end function

