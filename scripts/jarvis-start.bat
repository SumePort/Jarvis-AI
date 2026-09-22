@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo JARVIS virtual environment not found.
  exit /b 1
)
".venv\Scripts\python.exe" -m jarvis_v2.runtime.launcher
