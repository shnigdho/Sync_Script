' start_sync.vbs - Launches the sync script completely hidden
Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "pythonw.exe """ & strPath & "\sync_script.py""", 0, False