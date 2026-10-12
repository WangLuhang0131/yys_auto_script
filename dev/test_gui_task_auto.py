# -*- coding: utf-8 -*-
"""无人值守 GUI 测试：启动界面 -> 自动点「执行任务」-> 等任务结束 -> 打印结果 -> 退出。

用途：完整复现"从界面点执行"的路径，包括弹窗看门狗、runner、任务收尾。
"""
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

RUNTIME = float(sys.argv[1]) if len(sys.argv) > 1 else 100.0   # 最多跑多久

import tkinter as tk                                     # noqa: E402
from tkinter import ttk                                  # noqa: E402
import gui as gui_mod                                    # noqa: E402

print("=== 构建界面 ===", flush=True)
root = tk.Tk()
app = gui_mod.App(root)
print("界面已构建，任务数:", len(app.tasks) if hasattr(app, "tasks") else "?", flush=True)

# 找到「执行任务」按钮并点它（模拟用户点击）。注意界面用的是 ttk.Button！
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
print("找到执行按钮:", bool(start_btn), flush=True)
if start_btn is None:
    # 退而求其次：直接调 App 的启动方法
    print("改用 app._start() 启动", flush=True)

t0 = time.time()
state = {"clicked": False, "done": None}

# 主循环里插入：1 秒后点按钮，超时或结束后退出
def tick():
    if not state["clicked"] and time.time() - t0 > 1.0:
        state["clicked"] = True
        if start_btn:
            start_btn.invoke()
            print(">>> 已点击「执行任务」", flush=True)
        else:
            app._start()
            print(">>> 已调用 app._start()", flush=True)
    # 检测 runner 是否结束
    try:
        running = app.runner.running
    except Exception:
        running = False
    if state["clicked"] and not running and time.time() - t0 > 3:
        print(">>> 任务已结束", flush=True)
        state["done"] = True
        root.after(200, root.destroy)
        return
    if time.time() - t0 > RUNTIME:
        print(">>> 超时，强制退出", flush=True)
        try:
            app.runner.stop()
        except Exception:
            pass
        root.after(500, root.destroy)
        return
    root.after(200, tick)


root.after(200, tick)
root.mainloop()
print("\n=== 界面已关闭，跑了 %.1f 秒 ===" % (time.time() - t0), flush=True)
