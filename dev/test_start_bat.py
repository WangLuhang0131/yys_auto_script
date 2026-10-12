# -*- coding: utf-8 -*-
"""实测 start_gui.bat：能不能真的把界面启动起来（而不是闪退）。"""
import os
import subprocess
import sys
import time

BASE = r"D:\Program Files\WKSPC\yys"
print("=== 运行 start_gui.bat ===")
p = subprocess.Popen(["cmd", "/c", os.path.join(BASE, "start_gui.bat")],
                     cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     text=True, errors="replace")
time.sleep(15)

# bat 里用 start 启动 gui.py，所以要看有没有新的 python 进程
q = subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-Process python -ErrorAction SilentlyContinue | "
                    "Select-Object Id,StartTime,MainWindowTitle | "
                    "Format-Table -AutoSize | Out-String -Width 160"],
                   capture_output=True, text=True, timeout=60)
print("python 进程：")
print(q.stdout or "   （没有）")

print("=== bat 自己的输出 ===")
try:
    out = p.communicate(timeout=5)[0]
except Exception:
    p.kill()
    out = p.communicate()[0]
print(out if out and out.strip() else "   （没有输出，说明没走到报错分支）")

# 清理
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-Process python -ErrorAction SilentlyContinue | "
                "Where-Object { $_.MainWindowTitle -like '*阴阳师*' } | Stop-Process -Force"],
               capture_output=True, timeout=60)
print("\n已清理测试进程")
