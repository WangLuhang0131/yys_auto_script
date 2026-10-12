# -*- coding: utf-8 -*-
"""诊断"游戏开着却连不上 adb"：查进程、查 adb 服务稳定性、查端口。"""
import subprocess
import sys
import time

sys.path.insert(0, r"D:\Program Files\WKSPC\yys")
ADB = r"E:\MuMuPlayer\nx_main\adb.exe"


def sh(args, timeout=30):
    try:
        p = subprocess.run([ADB] + args, capture_output=True, text=True,
                           timeout=timeout, errors="replace")
        return (p.stdout or "").strip(), (p.stderr or "").strip()
    except Exception as e:
        return "", f"{type(e).__name__}: {e}"


print("=== 1) 前 15 个吃内存的进程（找模拟器）===")
out, _ = sh(["version"])
p = subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-Process | Sort-Object WorkingSet64 -Descending | "
                    "Select-Object -First 15 ProcessName,Id,"
                    "@{n='MB';e={[math]::Round($_.WorkingSet64/1MB,0)}} | "
                    "Format-Table -AutoSize | Out-String -Width 200"],
                   capture_output=True, text=True, timeout=60)
print(p.stdout)

print("=== 2) 连做 6 次 adb devices，看服务稳不稳 ===")
for i in range(6):
    o, e = sh(["devices"])
    first = o.splitlines()[-1] if o else "(空)"
    err = e.replace("\n", " ")[:70]
    print(f"  第{i+1}次: {first:32s} stderr={err}")
    time.sleep(2)

print("\n=== 3) 5037 端口监听情况 ===")
p = subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-NetTCPConnection -State Listen -LocalPort 5037 -ErrorAction SilentlyContinue | "
                    "Select-Object LocalAddress,LocalPort,OwningProcess | Format-Table -AutoSize | Out-String"],
                   capture_output=True, text=True, timeout=60)
print(p.stdout or "(无输出)")

print("=== 4) adb 进程 ===")
p = subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-Process -Name adb -ErrorAction SilentlyContinue | "
                    "Select-Object Id,StartTime,Path | Format-Table -AutoSize | Out-String -Width 200"],
                   capture_output=True, text=True, timeout=60)
print(p.stdout or "(没有 adb 进程)")

print("=== 5) 设备状态 ===")
o, e = sh(["devices"])
print(o)
