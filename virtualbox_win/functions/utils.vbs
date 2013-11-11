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

' This file contains additional functions


Function strip_quotes (str)
' Removes leading and/or trailing qoute if any
' Inputs: string
' Returns: string without qoutes
	if left(str,1) = """" then 
		str = right(str, len(str)-1)
	end if
	if right(str,1) = """" then 
		str = left(str, len(str)-1)
	end if
	strip_quotes = str
End Function
'wscript.echo strip_quotes ("""12345""")


function Find_And_Replace(strFilename, strFind, strReplace)
' Open strFilename, search for strFind and relace it with strReplace
' Returns: nothing
	dim objInputFile, strInputFile, objOutputFile, objRXP

	Set objInputFile = CreateObject("Scripting.FileSystemObject").OpenTextFile(strFilename, 1)
	strInputFile = objInputFile.ReadAll
	objInputFile.Close
	Set objInputFile = Nothing

	Set objOutputFile = CreateObject("Scripting.FileSystemObject").OpenTextFile(strFilename, 2, true)

	Set objRXP = New RegExp : objRXP.Global = True : objRXP.Multiline = True
	objRXP.Pattern = strFind

	objOutputFile.Write objRXP.Replace(strInputFile,  strReplace)
	objOutputFile.Close
	Set objOutputFile = Nothing
end function 
'Find_And_Replace "..\config.vbs", "host_nic_name\(0\) = .+$", "hostonly_interface_name=""HOIF name"""


function get_recent_file(strFolder,strFileExtention)
' Open strFolder and search for most recent file with extention strFileExtention
' Returns: string filename
	get_first_file = ""
	dim objFiles, objFile, maxDate
	On error resume next
	Set objFiles = CreateObject("Scripting.FileSystemObject").Getfolder(strFolder).Files
	for each objFile in objFiles
		if Right(objFile.name,len(strFileExtention)) = strFileExtention then
			if isempty(maxDate) or maxDate < objFile.DateCreated then
				maxDate = objFile.DateCreated
				get_first_file = strFolder & "\" & objFile.name
			end if
		end if 
	next
	on error goto 0
end Function
'wscript.echo get_first_file("..\iso\","iso")
