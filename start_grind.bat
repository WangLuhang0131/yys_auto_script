@echo off
chcp 65001 >nul
setlocal
title Onmyoji Guji Yanwu Auto Grind

rem ===== 1. locate python =====
set "PY="
if exist "C:\Users\PC\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" (
  set "PY=C:\Users\PC\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
)
if not defined PY (
  py -3 -c "pass" >nul 2>&1 && set "PY=py -3"
)
if not defined PY (
  python -c "pass" >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo.
  echo [ERROR] Python not found. Install Python 3 or edit the PY path in this file.
  echo.
  pause
  exit /b 1
)

set PYTHONUNBUFFERED=1

echo ============================================================
echo   Onmyoji  -  Guji Yanwu auto grind
echo ------------------------------------------------------------
echo   Before start, make sure:
echo     [1] MuMu emulator is running with Onmyoji open
echo     [2] Game is on the event screen (overview / detail / prep)
echo     [3] Do NOT minimize the emulator window
echo ============================================================
echo.

rem ===== 2. how many runs (Enter = 300) =====
set "RUNS="
set /p RUNS=How many runs? (press Enter for 300):
if not defined RUNS set "RUNS=300"

echo.
echo Will grind %RUNS% runs, about %RUNS% * 17 seconds.
echo To stop: close this window or press Ctrl+C.
echo.
pause

rem ===== 3. start =====
"%PY%" -u "%~dp0grind.py" --runs %RUNS% --yes %*
set "RC=%ERRORLEVEL%"

echo.
echo ============================================================
if "%RC%"=="0" (
  echo   Finished normally.
) else if "%RC%"=="1" (
  echo   Stopped early: challenge count may be used up, or the game
  echo   window could not be found. Check the log for the reason.
) else if "%RC%"=="2" (
  echo   Could not reach the battle prep page.
  echo   Make sure the game is on the event screen, then rerun.
) else (
  echo   Exit code = %RC%
)
echo   Logs: %~dp0logs\
echo ============================================================
echo.
pause
endlocal
