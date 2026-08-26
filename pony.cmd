@echo off
rem PONY launcher for Windows (bypasses PowerShell execution policy)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\pony.ps1" %*
