@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -X utf8 tools\youtube_upload.py setup
echo.
pause
