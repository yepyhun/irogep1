' Start-GUI.vbs — repo gyökérbe lép, rejtett indítás
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = base
sh.Run "cmd /c cd /d """ & base & """ && py -3 -m gui.app", 0
