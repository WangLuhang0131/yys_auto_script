# -*- coding: utf-8 -*-
"""GUI 冒烟测试：建窗口 -> 检查任务列表 -> 自动关闭。不执行任何任务。"""
import os
import sys
import traceback

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 项目根
sys.path.insert(0, _HERE)
os.chdir(_HERE)

import tkinter as tk
import gui

root = tk.Tk()
app = gui.App(root)
state = {}


def check():
    try:
        state["items"] = app.lb.size()
        state["current"] = getattr(app.current, "name", None)
        state["desc"] = app.desc_var.get()
        state["status"] = app.status_var.get()
        state["progress"] = app.progress_var.get()
    except Exception:
        state["err"] = traceback.format_exc()
    root.destroy()


root.after(700, check)
root.mainloop()

print("任务条目数:", state.get("items"))
print("当前选中:", state.get("current"))
print("状态栏:", state.get("status"), "| 进度:", state.get("progress"))
if state.get("err"):
    print("!! 出错:\n", state["err"])
