# -*- coding: utf-8 -*-
"""给 GUI 截个图（把窗口放到最前，用 adb 之外的 Windows 截屏做不到，
这里改用自绘：把窗口内容用 PostScript 导出再转）。简化做法：
用 ctypes 抓整个屏幕，再裁剪窗口区域。"""
import os
import sys
import time
import ctypes
import tkinter as tk

# 让抓屏进程按物理像素工作（否则高 DPI 下会缩放错位）
for _fn in (lambda: ctypes.windll.shcore.SetProcessDpiAwareness(2),
            lambda: ctypes.windll.user32.SetProcessDPIAware()):
    try:
        _fn()
        break
    except Exception:
        pass

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)
os.chdir(_HERE)

import gui  # noqa: E402

root = tk.Tk()

app = gui.App(root)
root.geometry("1060x700+40+20")
# 塞几条假日志，模拟运行中的样子
for line, tag in [
    ("[10:31:05] === 任务开始：活动副本（古迹演武） ===", None),
    ("[10:31:06] 检查通过：已就位（古迹演武备战页）", None),
    ("[10:31:07] --- 第 3/300 次 ---", None),
    ("[10:31:07]     点击 challenge -> (1722,858) 挑战", None),
    ("[10:31:18]   检测到结束画面（分数 0.992，战斗耗时 10.3s），立刻点击继续", None),
    ("[10:31:19]   本轮完成，用时 16.3s", None),
    ("[10:31:19]     成功  用时 16.3s  累计成功 3 失败 0", "ok"),
    ("[10:31:20] --- 第 4/300 次 ---", None),
    ("[10:31:20] !! 挑战键已变灰，活动道具用完 → 任务完成", "err"),
]:
    app._append(line, tag)
app.progress_var.set("活动战斗 (3/300)")
app.status_var.set("运行中…")
app.start_btn.configure(state="disabled")
app.stop_btn.configure(state="normal")

root.update()
root.lift()
root.attributes("-topmost", True)
root.update()
time.sleep(1.0)
root.update()

# 抓屏并裁剪窗口区域
user32 = ctypes.windll.user32
hwnd = int(root.frame(), 16) if isinstance(root.frame(), str) else root.winfo_id()
rect = ctypes.wintypes.RECT() if hasattr(ctypes, "wintypes") else None

from ctypes import wintypes  # noqa: E402
r = wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(r))
w, h = r.right - r.left, r.bottom - r.top
print("窗口区域:", r.left, r.top, w, h)

# 用 Powershell 之外的方式：直接抓屏
import subprocess
out = os.path.join(_HERE, "shots", "gui_preview.png")
ps = f'''
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap {w}, {h}
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen({r.left}, {r.top}, 0, 0, $bmp.Size)
$bmp.Save("{out}", [System.Drawing.Imaging.ImageFormat]::Png)
'''
subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)
print("saved", out, os.path.exists(out))
root.destroy()
