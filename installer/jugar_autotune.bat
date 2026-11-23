@echo off
rem Pon este archivo y psx_autotune.ps1 junto a psxrecomp.exe y settings.toml.
rem Para un exe con otro nombre: jugar_autotune.bat "ruta\juego.exe"
set "EXE=%~1"
if "%EXE%"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0psx_autotune.ps1"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0psx_autotune.ps1" -Exe "%EXE%"
)
pause
