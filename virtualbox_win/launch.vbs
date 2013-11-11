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


Sub Import(strFile)
	Dim objFS, objFile, strCode
	Set objFS = CreateObject("Scripting.FileSystemObject")
	Set objFile = objFS.OpenTextFile(strFile)
	strCode = objFile.ReadAll
	objFile.Close
	ExecuteGlobal strCode
End Sub
Import ".\functions\vm.vbs"
Import ".\functions\network.vbs"
Import ".\functions\utils.vbs"
Import ".\functions\product.vbs"
Import "config.vbs"

' check for files and prepare varables
Import ".\actions\prepare-environment.vbs"

' clean previous installation if exists
'Import ".\actions\clean-previous-installation.vbs"

' clean previous installation if exists
'Import ".\actions\create-interfaces.vbs"

' Environment preparation is done
wscript.echo "Setup is done."

' Create and launch master node
'Import ".\actions\master-node-create-and-install.vbs"

' Create and launch slave nodes
'Import ".\actions\slave-nodes-create-and-boot.vbs"

