@echo off
chcp 65001 >nul
title 焊接设备AI Agent - 前端界面

cd /d "c:\Users\Administrator\Downloads\FirstAgent\web"

echo ==========================================
echo   启动 React 前端界面
echo ==========================================

:: 释放端口
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo 释放端口 3000 (PID: %%a)
    taskkill /f /pid %%a >nul 2>&1
)

if not exist "node_modules\" (
    echo 安装依赖...
    call npm install
)

echo 构建生产版本...
call npx vite build

echo.
echo 启动前端...
echo 前端地址: http://localhost:3000
echo.
call npx vite preview --port 3000 --host 0.0.0.0

pause
