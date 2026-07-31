@echo off
chcp 65001 >nul
title 焊接设备AI Agent - 后端服务

set "PATH=%USERPROFILE%\.local\bin;%PATH%"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
cd /d "c:\Users\Administrator\Downloads\FirstAgent"

echo ==========================================
echo   启动后端 API 服务
echo ==========================================

:: 释放端口
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo 释放端口 8000 (PID: %%a)
    taskkill /f /pid %%a >nul 2>&1
)

echo 服务地址: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo.

uv run python -m uvicorn src.api.server:app --port 8000 --host 0.0.0.0

pause
