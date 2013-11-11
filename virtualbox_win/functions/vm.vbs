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

'This file contains the functions to manage VMs through VirtualBox CLI


Dim objFSO, objShell, VBoxManagePath
Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objShell = WScript.CreateObject("WScript.Shell")
' use this VBoxManagePath initialization for debuging vm.vbs only
' VBoxManagePath = """C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"""

function get_vbox_value (strCommand, strParameter)
' Parse output of given command and returns value of given parameter. If there is several values its separated by CR LF.
' Inputs: strCommand - VBoxManage.exe command
'		strParameter - name of parameter exactly from start of line to colon.
' Returns: string separated by CR LF.
	Dim ret, objMatches, objRXP, strLines, strLine, strValue

	Set objRXP = New RegExp : objRXP.Global = True : objRXP.Multiline = False
	objRXP.Pattern = "^" + strParameter + ":?\s*(.+)$"

	ret = call_VBoxManage(strCommand)
	strLines = split(ret(1),vbCrLf)
	for each strLine in strLines
		set objMatches = objRXP.Execute(strLine)
		if objMatches.count > 0 then
			' there could be parentheses in strParameter therefore we must catch value this awkward way
			strValue = objMatches(0).SubMatches(objMatches(0).SubMatches.count-1)
			if isempty(get_vbox_value) then
				get_vbox_value = strValue
			else
				get_vbox_value = get_vbox_value + vbCrLf + strValue
			end if
		end if
	next
	'get_vbox_value = strValue
end Function 
' WScript.Echo "Value is " + get_vbox_value ("list systemproperties", "Default machine folder")
' WScript.Echo "Value is " + get_vbox_value ("list hostonlyifs", "Name")


function get_vm_base_path ()
' Returns name of folder there VMs are stored. 
' Example: "D:\VirtualBox VMs" (without qoutes)
	get_vm_base_path = get_vbox_value ("list systemproperties", "Default machine folder")
end Function


function get_vms_list (strCommand)
' Reads list of VMs
' Inputs: strCommand should be one of strings: "list vms", "list runningvms"
' Returns: an array of pairs (VM_name, VM_UUID)
	Dim ret, lstProgID, objMatches , objMatch, objRXP

	' get_vms_list = Nothing

	Set objRXP = New RegExp : objRXP.Global = True : objRXP.MultiLine = True
	objRXP.Pattern = """([^""]+)""\s+({[^}]+})"
	Set lstProgID = CreateObject( "System.Collections.ArrayList" )

	ret = call_VBoxManage(strCommand)
	set objMatches = objRXP.Execute(ret(1)) 
	if objMatches.count > 0 then
		for each objMatch in objMatches
	 		lstProgID.Add objMatch.SubMatches
		next
		get_vms_list = lstProgID.ToArray
	end if
end Function 
' dim list, str, l
' list = get_vms_list ("list vms")
' str=""
' if isEmpty(list) then
' 	WScript.Echo "No vms"
' else
' 	for each l in list
' 		str= str + l(0) + "___" + l(1) + vbCrLf
' 	next 
' 	WScript.Echo "vms: " + str
' end if


function get_vms_present()
' Returns list of existing VMs
' Returns: an array of pairs (VM_name, VM_UUID)
	get_vms_present = get_vms_list ("list vms")
end Function


Function get_vms_running()
' Returns list of running VMs
' Returns: an array of pairs (VM_name, VM_UUID)
	get_vms_running = get_vms_list ("list runningvms")
end Function


function is_vm_present(strVmName)
' Returns: boolean True if VM exists, False if VM not exists
	dim arrVMs , isPresent , VmPair
	
	isPresent = False

	arrVMs = get_vms_present()
	if not isEmpty(arrVMs) then
		for each VmPair in arrVMs
			if strVmName = VmPair(0) then 
				isPresent = true
			end if
		next 
	end if

	is_vm_present = isPresent
end Function


function is_vm_running(strVmName)
' Returns: boolean True if VM is running, False if VM is not running
	dim arrVMs , isRunning , VmPair
	
	isRunning = False

	arrVMs = get_vms_running()
	if not isEmpty(arrVMs) then
		for each VmPair in arrVMs
			if strVmName = VmPair(0) then 
				isRunning = true
			end if
		next 
	end if

	is_vm_running = isRunning
end Function
' if is_vm_running("fuel2-pm")= True then
' 	WScript.Echo "is_vm_running(fuel2-pm)= True"
' end if


Function call_VBoxManage (strCommand)
' executes VBoxManage.exe with given command.
' Returns: array, where arr(0) is VBoxManage ExitCode
' 			arr(1) - VBoxManage StdOut
' 			arr(2) - VBoxManage StdErr
	dim oExec
	dim arr(2)
	Set oExec = objShell.Exec(VBoxManagePath + " " + strCommand)
	arr(1) = ""
	arr(2) = ""

	Do While oExec.Status = 0
		If Not oExec.StdOut.AtEndOfStream Then
			arr(1) = arr(1) & oExec.StdOut.ReadAll
		End If

		If Not oExec.StdErr.AtEndOfStream Then
			arr(2) = arr(2) & oExec.StdErr.ReadAll
		End If
		WScript.Sleep 100
	Loop
	arr(0) = oExec.ExitCode

	if oExec.ExitCode <> 0 then
		WScript.Echo "Error occured in command:" + vbCrLf + "VBoxManage " + strCommand
		WScript.Echo "stderr:" + vbCrLf + arr(2)
		WScript.Echo "stdout:" + vbCrLf + arr(1)
	end if
	call_VBoxManage = arr
End Function
' ret = call_VBoxManage ("list systemproperties")
' wscript.echo ret(1)


Function create_vm (strVmName, strNetName, intCpuCores, intMemSize, intDiskSize)
' creates VM with given parameters
' Inputs: strVmName - string
'			strNetName - string, name of network interface to connect to VM
'			intCpuCores - integer number of cores for VM
'			intMemSize - integer amount of memory in MB
'			intDiskSize - integer disk size in MB
' Returns: nothing
	dim objExec, cmd

	' Create virtual machine with the right name and type (assuming CentOS) 
	'VBoxManage createvm --name $strVmName --ostype RedHat_64 --register
	cmd = " createvm --name """ + strVmName + """ --ostype RedHat_64 --register"
	call_VBoxManage cmd

	' Set the real-time clock (RTC) operate in UTC time
	' Set memory and CPU parameters
	' Set video memory to 16MB, so VirtualBox does not complain about "non-optimal" settings in the UI
	'VBoxManage modifyvm $strVmName --rtcuseutc on --memory $intMemSize --cpus $intCpuCores --vram 16
	cmd = " modifyvm """ + strVmName + """ --rtcuseutc on --memory " & intMemSize & " --cpus " & intCpuCores & " --vram 16"
	call_VBoxManage cmd
	
	' Configure main network interface
	add_hostonly_adapter_to_vm strVmName, 1, strNetName
	
	' Configure storage controllers
	'VBoxManage storagectl $strVmName --name 'IDE' --add ide
	cmd = " storagectl """ + strVmName + """ --name ""IDE"" --add ide --hostiocache on"
	call_VBoxManage cmd
	'VBoxManage storagectl $strVmName --name 'SATA' --add sata
	cmd = " storagectl """ + strVmName + """ --name ""SATA"" --add sata --hostiocache on"
	call_VBoxManage cmd
	
	' Create and attach the main hard drive
	add_disk_to_vm strVmName, 0, intDiskSize
end Function
' ret = create_vm("foo", "VirtualBox Host-Only Ethernet Adapter #8" ,1 , 512, 8192)


Function add_hostonly_adapter_to_vm(strVmName, intNicId, strNetName)
' add host-only network interface to VM with given name.
' Inputs: strVmName - VM name 
' 		intNicId - NIC number in VM. Possible values from 1 to 4
'		strNetName - host-only network name
' Returns: nothing
	WScript.echo "Adding hostonly adapter to """ + strVmName + """ and bridging with host NIC " + strNetName + "..."
	dim cmd
	' Add Intel PRO/1000 MT Desktop (82540EM) card to VM. The card is 1Gbps.
	'VBoxManage modifyvm $strVmName --nic${intNicId} hostonly --hostonlyadapter${intNicId} $nic --nictype${intNicId} 82540EM --cableconnected${intNicId} on --macaddress${intNicId} auto
	cmd = " modifyvm """ + strVmName + """ --nic" & intNicId & " hostonly --hostonlyadapter" & intNicId & " """ & strNetName & """ --nictype" & intNicId & " 82540EM --cableconnected" & intNicId & " on --macaddress" & intNicId & " auto"
	call_VBoxManage cmd
	'VBoxManage modifyvm  $name  --nicpromisc${id} allow-all
	cmd = "modifyvm """ + strVmName + """ --nicpromisc" & intNicId & " allow-all"
	call_VBoxManage cmd
	'VBoxManage controlvm $strVmName setlinkstate${intNicId} on
	cmd = " controlvm """ + strVmName + """ setlinkstate" & intNicId & " on"
	call_VBoxManage cmd
end Function


Function add_nat_adapter_to_vm(strVmName, intNicId, strNetName)
' add NAT network interface to VM with given name.
' Inputs: strVmName - VM name 
' 		intNicId - NIC number in VM. Possible values from 1 to 4
'		strNetName - NAT network name
' Returns: nothing
	WScript.echo "Adding NAT adapter to """ + strVmName + """ for outbound network access through the host system..."
	dim cmd
	' Add Intel PRO/1000 MT Desktop (82540EM) card to VM. The card is 1Gbps.
	'VBoxManage modifyvm $name --nic${id} nat --nictype${id} 82540EM --cableconnected${id} on --macaddress${id} auto --natnet${id} "${nat_network}"
	cmd = " modifyvm """ + strVmName + """ --nic" & intNicId & " nat --nictype" & intNicId & " 82540EM --cableconnected" & intNicId & " on --macaddress" & intNicId & " auto --natnet" & intNicId & " """ & strNetName & """"
	call_VBoxManage cmd
	'VBoxManage modifyvm  $name  --nicpromisc${id} allow-all
	cmd = "modifyvm """ + strVmName + """ --nicpromisc" & intNicId & " allow-all"
	call_VBoxManage cmd
	'VBoxManage controlvm $strVmName setlinkstate${intNicId} on
	cmd = " controlvm """ + strVmName + """ setlinkstate" & intNicId & " on"
	call_VBoxManage cmd
end Function


function add_disk_to_vm(strVmName, intPort, intDiskSize)
' Creates disk with size intDiskSize and attaches it to VM
' Inputs: strVmName - VM name
'		intPort - VM's SATA port number to connect disk to
'		intDiskSize - disk size in MB
' Returns: nothing
	dim strVmBasePath, strVmDiskPath, strDiskName, strDiskFilename
	strVmBasePath = get_vm_base_path()
	strVmDiskPath = objFSO.BuildPath(strVmBasePath, strVmName) 
	strDiskName = strVmName & "_" & intPort
	strDiskFilename = strDiskName & ".vdi"
	
	wscript.echo "Adding disk to """ + strVmName + """, with size " & intDiskSize & " Mb..."
	dim cmd
	'VBoxManage createhd --filename "$strVmDiskPath/$strDiskName" --size $intDiskSize --format VDI
	cmd = " createhd --filename """ + objFSO.BuildPath(strVmDiskPath, strDiskName) + """ --size " & intDiskSize & " --format VDI"
	WScript.echo cmd
	call_VBoxManage cmd
	'VBoxManage storageattach $strVmName --storagectl 'SATA' --port $intPort --device 0 --type hdd --medium "$strVmDiskPath/$strDiskFilename"
	cmd = " storageattach """ + strVmName + """ --storagectl ""SATA"" --port " & intPort & " --device 0 --type hdd --medium """ + objFSO.BuildPath(strVmDiskPath,strDiskFilename) + """ "
	WScript.echo cmd
	call_VBoxManage cmd
end function


Function delete_vm(strVmName)
' Powers off and deletes VM
' Returns: nothing
	dim strVmBasePath, strVmPath
	strVmBasePath = get_vm_base_path()
	strVmPath = objFSO.BuildPath(strVmBasePath, strVmName) 

	dim cmd

	' Power off VM, if it's running
	if is_vm_running(strVmName) then
		cmd = "controlvm " + strVmName + " poweroff"
		call_VBoxManage cmd
	end if

	' Virtualbox does not fully delete VM file structure, so we need to delete the corresponding directory with files as well 

	wscript.echo "Deleting existing virtual machine " + strVmName + "..."
	cmd = "unregistervm " + strVmName + " --delete"
	call_VBoxManage cmd
	if objFSO.FolderExists(strVmPath) then
		on error resume next
		objFSO.DeleteFolder strVmPath, True
		On Error GoTo 0
	end if
End Function


Function delete_vms_multiple(strVmNamePrefix)
' powers of and deletes all VM with given name prefix
' Returns: nothing
	dim arrVMs, intPrefixLen, arrVM
	arrVMs = get_vms_present()
	if not isEmpty(arrVMs) then
		intPrefixLen=len(strVmNamePrefix)
		
		' Loop over the array arrVMs and delete them, if its name matches the given refix 
		for each arrVM in arrVMs 
			dim strLeft
			strLeft = left(arrVM(0), intPrefixLen)
			if strLeft = strVmNamePrefix then
				wscript.echo "Found existing VM: " + arrVM(0) + ". Deleting it..."
				delete_vm arrVM(0)
			end if
		next
	end if
End Function
'delete_vms_multiple "foo"


Function start_vm (strVmName)
' Just start VM
' Returns: nothing
	'call_VBoxManage "startvm """ + strVmName + """ --type headless"
	call_VBoxManage "startvm """ + strVmName + """"
End Function


Function mount_iso_to_vm(strVmName, strIsoPath)
' Mount ISO to the VM
' Returns: nothing
	call_VBoxManage "storageattach """ + strVmName + """ --storagectl ""IDE"" --port 0 --device 0 --type dvddrive --medium """ + strIsoPath + """"
End Function
' mount_iso_to_vm "foo", "D:\distr\iso\Ubuntu-x86_64-mini.iso"


Function enable_network_boot_for_vm(strVmName)
' Set the right boot priority
' Returns: nothing
	call_VBoxManage "modifyvm """ + strVmName + """ --boot1 disk --boot2 net --boot3 none --boot4 none --nicbootprio1 1"
End Function
' enable_network_boot_for_vm "foo"
' start_vm "foo"
' delete_vms_multiple "foo"
