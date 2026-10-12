@echo off
chcp 65001 >nul
setlocal
title Onmyoji Script Console

rem ===== 找 Python =====
rem 坑：PATH 里的 python.EXE 可能是微软商店的占位程序，
rem     用 "python -c pass" 检测会误判成功，但它其实不执行脚本（窗口一闪就没）。
rem     所以这里用 "能不能真的导入 tkinter/PIL/numpy" 来判定。
set "PY="

rem 1) 同目录自带的（打包给别人时用）
if exist "%~dp0python\python.exe" (
  "%~dp0python\python.exe" -c "import tkinter,PIL,numpy" >nul 2>&1 && set "PY=%~dp0python\python.exe"
)

rem 2) py 启动器
if not defined PY (
  py -3 -c "import tkinter,PIL,numpy" >nul 2>&1 && set "PY=py -3"
)

rem 3) PATH 里的 python
if not defined PY (
  python -c "import tkinter,PIL,numpy" >nul 2>&1 && set "PY=python"
)

rem 4) 本机已知的真实 Python 位置
if not defined PY (
  for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Users\PC\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
  ) do (
    if not defined PY if exist %%P (
      %%P -c "import tkinter,PIL,numpy" >nul 2>&1 && set "PY=%%~P"
    )
  )
)

if not defined PY (
  echo.
  echo [错误] 找不到可用的 Python。
  echo.
  echo 常见原因：PATH 里的 python 是「微软商店」的占位程序，它不执行脚本。
  echo.
  echo 解决办法（任选一个）：
  echo   1. 安装官方 Python 3.10+：https://www.python.org/downloads/
  echo      安装时务必勾选 "Add python.exe to PATH"
  echo   2. 或者把便携版 Python 解压到本目录下的 python\ 文件夹
  echo      （即 python\python.exe 存在）
  echo.
  pause
  exit /b 1
)

set PYTHONUNBUFFERED=1
cd /d "%~dp0"
start "" %PY% -u "%~dp0gui.py"
endlocal
