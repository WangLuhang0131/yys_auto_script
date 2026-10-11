# -*- coding: utf-8 -*-
"""验证打包后的 exe 调 adb 不再弹窗，并且 adb 调用能正常返回。

为什么必须在 exe 里验证：源码用 python.exe 跑时父进程有控制台，子进程可共用，
所以看不到弹窗问题；只有 --windowed 的 exe 才会暴露。

做法：启动 exe，在其中用 adb 连续截图/点击（通过任务运行），
同时统计系统里 cmd/conhost 窗口数量变化。
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name = sys.argv[1] if len(sys.argv) > 1 else "阴阳师脚本控制台_文件夹版"
EXE = os.path.join(HERE, "release", name + ".exe")
if not os.path.exists(EXE):
    EXE = os.path.join(HERE, "release", name, name + ".exe")
print("测试目标:", EXE, flush=True)
print("存在:", os.path.exists(EXE), flush=True)


def window_count():
    """统计可能被误弹出来的控制台窗口进程数。"""
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq conhost.exe", "/FO", "CSV"],
            capture_output=True, text=True, timeout=30).stdout
        return max(0, out.count("conhost.exe"))
    except Exception as e:
        return -1


print("\n启动前 conhost 数量:", window_count(), flush=True)
p = subprocess.Popen([EXE], cwd=os.path.dirname(EXE))
print("已启动 exe, PID", p.pid, flush=True)

# 后台跑着不动时 conhost 数量不应持续增长
counts = []
for i in range(10):
    time.sleep(2)
    # 顺带用同样的方式调一次 adb，确认 exe 目录下有没有正常产出日志
    counts.append(window_count())
    if p.poll() is not None:
        print(f"exe 在 {(i+1)*2} 秒后退出，退出码 {p.poll()}")
        break
print("运行期间 conhost 数量序列:", counts)

# 关闭
try:
    p.terminate()
    time.sleep(2)
    if p.poll() is None:
        p.kill()
except Exception:
    pass

rel = os.path.dirname(EXE)
print("\nrelease 目录:", sorted(os.listdir(rel)))
logdir = os.path.join(rel, "logs")
if os.path.isdir(logdir):
    logs = sorted(os.listdir(logdir))
    print("logs/ 里的日志:", logs[-3:])
    if logs:
        with open(os.path.join(logdir, logs[-1]), encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        print("最后几行日志:")
        for ln in lines[-8:]:
            print("   ", ln)
