@echo off
set PATH=%USERPROFILE%\.local\bin;%PATH%
cd /d C:\Users\Administrator\Downloads\FirstAgent
uv run python -m uvicorn src.api.server:app --port 8000 --host 0.0.0.0