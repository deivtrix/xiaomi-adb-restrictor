@echo off
set "PATH=%~dp0adb;%PATH%"
python "%~dp0dkma-monster\gui\server.py"
pause
