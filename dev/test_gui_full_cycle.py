# -*- coding: utf-8 -*-
"""无人值守 GUI 测试：从界面点「执行任务」，跑到任务自然结束，验证全链路。

和 test_gui_task_auto.py 的区别：这里把目标次数改小（默认 1），
所以是**跑到任务自己收尾**，能验证"开始 -> 打 -> 收工 -> 回庭院"完整闭环。
"""
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LIMIT = float(sys.argv[2]) if len(sys.argv) > 2 else 180.0

import tkinter as tk                                     # noqa: E402
import gui as gui_mod                                    # noqa: E402

root = tk.Tk()
app = gui_mod.App(root)
print("界面已构建", flush=True)

# 把目标次数改成 RUNS
try:
    app.runs_var.set(str(RUNS))
    print(f"目标次数设为 {RUNS}", flush=True)
except Exception as e:
    print("设置次数失败:", e, flush=True)


def find_button(widget, text):
    try:
        cls = widget.winfo_class()
    except Exception:
        cls = ""
    if cls in ("Button", "TButton"):
        try:
            if text in str(widget.cget("text")):
                return widget
        except Exception:
            pass
    for ch in widget.winfo_children():
        r = find_button(ch, text)
        if r:
            return r
    return None


start_btn = find_button(root, "执行任务")
t0 = time.time()
state = {"clicked": False, "logs": []}

# 同时把日志抓下来（界面日志走队列，这里直接读 log 文件更省事）
logdir = os.path.join(_ROOT, "logs")
before = set(os.listdir(logdir)) if os.path.isdir(logdir) else set()


def tick():
    if not state["clicked"] and time.time() - t0 > 1.0:
        state["clicked"] = True
        if start_btn:
            start_btn.invoke()
        else:
            app._start()
        print(">>> 已点击「执行任务」", flush=True)

    running = False
    try:
        running = app.runner.running
    except Exception:
        pass

    if state["clicked"] and not running and time.time() - t0 > 4:
        print(">>> 任务已自然结束，用时 %.1fs" % (time.time() - t0), flush=True)
        root.after(200, root.destroy)
        return
    if time.time() - t0 > LIMIT:
        print(">>> 到时限，停止任务", flush=True)
        try:
            app.runner.stop()
        except Exception:
            pass
        root.after(1500, root.destroy)
        return
    root.after(200, tick)


root.after(200, tick)
root.mainloop()

# 打印这次跑出来的日志
after = set(os.listdir(logdir)) if os.path.isdir(logdir) else set()
new = sorted(after - before)
print("\n=== 本次产生的日志 ===", flush=True)
for name in new:
    p = os.path.join(logdir, name)
    print(f"--- {name} ---", flush=True)
    with open(p, encoding="utf-8", errors="replace") as f:
        print(f.read(), flush=True)
