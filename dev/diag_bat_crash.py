# -*- coding: utf-8 -*-
"""诊断 start_gui.bat 为什么闪退：模拟 bat 的查找逻辑，并真跑一次 gui.py 抓错误。"""
import os
import shutil
import subprocess
import sys
import time

BASE = r"D:\Program Files\WKSPC\yys"
print("=== 1) 模拟 bat 的查找逻辑 ===")
cands = [
    (os.path.join(BASE, "python", "python.exe"), "自带的 python\\python.exe"),
    (shutil.which("python"), "PATH 里的 python"),
    (shutil.which("py"), "PATH 里的 py 启动器"),
    (r"C:\Users\PC\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe",
     "DSH 运行时 python"),
]
for p, label in cands:
    print(f"   {label:28s} -> {p if p else '（找不到）'}")

print("\n=== 2) 真跑一遍 gui.py，把输出写文件 ===")
PY = r"C:\Users\PC\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
logp = os.path.join(BASE, "build_tmp", "gui_start.log")
os.makedirs(os.path.dirname(logp), exist_ok=True)
with open(logp, "w", encoding="utf-8") as f:
    p = subprocess.Popen([PY, "-u", os.path.join(BASE, "gui.py")],
                         cwd=BASE, stdout=f, stderr=subprocess.STDOUT)
print("   已启动 PID", p.pid)
time.sleep(10)
alive = p.poll() is None
print("   10 秒后进程存活:", alive, "| 退出码:", p.poll())
if alive:
    p.terminate()
    time.sleep(2)
    if p.poll() is None:
        p.kill()
print("\n=== 3) gui.py 的输出 ===")
with open(logp, encoding="utf-8", errors="replace") as f:
    txt = f.read()
print(txt if txt.strip() else "(没有输出)")

print("=== 4) 开始菜单/注册表里有没有 python ===")
for c in ("python", "python3", "py"):
    print(f"   which {c}: {shutil.which(c)}")
