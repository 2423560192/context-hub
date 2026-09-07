@echo off
setlocal
title SkillHub MCP Server (shared HTTP)

cd /d "%~dp0.."

rem Usage: start-skillhub-mcp.bat [knowledge-repo-path] [port]
set "REPO=%~1"
if "%REPO%"=="" set "REPO=%CD%"
set "PORT=%~2"
if "%PORT%"=="" set "PORT=8765"

if not exist "%REPO%\knowledge\" (
  echo [ERROR] No "knowledge" directory found under: %REPO%
  echo.
  echo Pass the path to YOUR knowledge repo as the first argument. Example:
  echo   start-skillhub-mcp.bat D:\MySkills\my-knowledge-repo 8765
  pause
  exit /b 1
)

where uv >nul 2>&1
if errorlevel 1 (
  echo [ERROR] uv was not found on PATH.
  echo Install it from https://docs.astral.sh/uv/ first, then retry.
  pause
  exit /b 1
)

echo ============================================
echo  SkillHub MCP server - shared HTTP mode
echo  Knowledge repo: %REPO%
echo  Endpoint:       http://127.0.0.1:%PORT%/mcp
echo  Press Ctrl+C to stop.
echo ============================================
echo.

uv run skillhub-mcp --repo "%REPO%" --transport streamable-http --host 127.0.0.1 --port %PORT%
set "code=%errorlevel%"

if not "%code%"=="0" (
  echo.
  echo [ERROR] Server exited with code %code%. See the log above.
  pause
)
endlocal
