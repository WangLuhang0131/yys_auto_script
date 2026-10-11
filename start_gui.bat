@echo off
chcp 65001 >nul
setlocal
title Onmyoji Script Console

rem ===== 找 Python：优先用同目录自带的（打包给别人时自带解释器） =====
set "PY="
if exist "%~dp0python\python.exe" set "PY=%~dp0python\python.exe"
if not defined PY (
  py -3 -c "pass" >nul 2>&1 && set "PY=py -3"
)
if not defined PY (
  python -c "pass" >nul 2>&1 && set "PY=python"
)
if not defined PY (
  if exist "C:\Users\PC\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" (
    set "PY=C:\Users\PC\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
  )
)
if not defined PY (
  echo.
  echo [ERROR] 找不到 Python。
  echo         请安装 Python 3.10+（安装时勾选 Add to PATH），
  echo         或把便携版 Python 放到本目录的 python\ 文件夹里。
  echo.
  pause
  exit /b 1
)

set PYTHONUNBUFFERED=1
start "" "%PY%" -u "%~dp0gui.py"
endlocal
