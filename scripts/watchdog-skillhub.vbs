Set shell = CreateObject("WScript.Shell")
shell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -File ""D:\Projects\context-hub\scripts\watchdog-skillhub.ps1""", 0, False
