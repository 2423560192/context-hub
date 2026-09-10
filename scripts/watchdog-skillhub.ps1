$ErrorActionPreference = 'SilentlyContinue'

$listener = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
if ($listener) { exit 0 }

$lock = Join-Path $env:TEMP 'skillhub-watchdog.lock'
if (Test-Path $lock) {
    if ((Get-Item $lock).LastWriteTime -gt (Get-Date).AddMinutes(-1)) { exit 0 }
}
Set-Content -Path $lock -Value (Get-Date).ToString('o') -Encoding ASCII

Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','uv run skillhub-mcp --repo d:\Projects\my-skills --transport streamable-http --host 127.0.0.1 --port 8765' -WorkingDirectory 'D:\Projects\context-hub' -WindowStyle Hidden
