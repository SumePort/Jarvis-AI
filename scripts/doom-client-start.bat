@echo off
setlocal
cd /d "%~dp0"
python -m doom.client start
endlocal
