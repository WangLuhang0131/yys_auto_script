# -*- coding: utf-8 -*-
"""用 Python 非阻塞地验证 exe：启动 -> 看进程在不在 -> 看自检日志 -> 关掉。

PowerShell 的 Start-Process -PassThru 在这个沙箱里会挂住，所以用 Python 的
subprocess.Popen（不阻塞）来做。
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name = sys.argv[1] if len(sys.argv) > 1 else "阴阳师脚本控制台"
EXE = os.path.join(HERE, "release", name + ".exe")
if not os.path.exists(EXE):
    EXE = os.path.join(HERE, "release", name, name + ".exe")   # onedir 形式
LOGF = os.path.join(os.path.dirname(EXE), "selftest.log")

print("exe 存在:", os.path.exists(EXE))
if not os.path.exists(EXE):
    sys.exit(1)

# 1) 先跑自检（windowed exe 也能把结果写文件）
if os.path.exists(LOGF):
    os.remove(LOGF)
p = subprocess.Popen([EXE, "--selftest"], cwd=os.path.dirname(EXE))
print("已启动 --selftest, PID", p.pid)
for _ in range(40):
    if p.poll() is not None:
        break
    time.sleep(0.5)
print("自检进程退出码:", p.poll())
if os.path.exists(LOGF):
    print("\n--- selftest.log ---")
    with open(LOGF, encoding="utf-8", errors="replace") as f:
        print(f.read())
else:
    print("!! 没有生成 selftest.log")

# 2) 再启动真正的 GUI，看进程是否存活
print("\n=== 启动 GUI ===", flush=True)
g = subprocess.Popen([EXE], cwd=os.path.dirname(EXE))
alive = False
for i in range(30):
    time.sleep(1)
    rc = g.poll()
    if rc is not None:
        print(f"GUI 进程在 {i+1} 秒后退出，退出码 {rc}")
        break
    if i == 11:
        alive = True
        print("GUI 进程已存活 12 秒（正常，说明能起来）")
else:
    alive = g.poll() is None

# 看看有没有子进程（onefile 会有个解包子进程）
if alive:
    print("进程状态: 存活")
try:
    g.terminate()
    time.sleep(2)
    if g.poll() is None:
        g.kill()
    print("已关闭 GUI")
except Exception as e:
    print("关闭时出错:", e)

# 3) 检查 exe 目录有没有生成 logs/ 等可写目录
rel = os.path.dirname(EXE)
print("\nrelease 目录内容:", sorted(os.listdir(rel)))
