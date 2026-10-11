# -*- coding: utf-8 -*-
"""
阴阳师脚本 桌面控制台
=====================
左边：选任务 + 设定次数 + 执行 / 结束任务
右边：实时日志，顶部显示「战斗(3/9)」这种进度

启动：python gui.py   （或双击 start_gui.bat）

界面会自动扫描 tasks/ 目录：新增一个任务文件夹就多一个选项，
删掉某个任务文件夹也不会影响其它任务。
"""
from __future__ import annotations

import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# 打包成 exe 后：把可写目录设为 exe 所在目录，并切过去（日志、截图都落在那里）
try:
    from core.paths import app_root, ensure_app_dirs
    _APP = app_root()
    if _APP not in sys.path:
        sys.path.insert(0, _APP)
    ensure_app_dirs()
    os.chdir(_APP)
except Exception:
    _APP = HERE

import core                                   # noqa: E402
from core.runner import TaskRunner            # noqa: E402

APP_TITLE = "阴阳师脚本控制台"
APP_ROOT = _APP
MAX_LOG_LINES = 2000


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.runner = TaskRunner(logdir=os.path.join(APP_ROOT, "logs"))
        self.tasks = []            # [(目录名, 类)]
        self.current = None
        self.log_lines = 0

        root.title(APP_TITLE)
        # 窗口尺寸自适应屏幕（避免高分辨率缩放导致底部按钮被顶出屏幕）
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w = min(1120, max(880, sw - 120))
        h = min(760, max(560, sh - 220))
        root.geometry(f"{w}x{h}+{max(20, (sw - w) // 2)}+{max(20, (sh - h) // 3)}")
        root.minsize(860, 520)

        self._build_ui()
        self._reload_tasks()
        self._tick()

    # ================= UI =================
    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=8)
        outer.pack(fill="both", expand=True)

        left = ttk.Frame(outer, width=300)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        # ---- 底部操作区先占位，保证永远可见 ----
        bottom = ttk.Frame(left)
        bottom.pack(side="bottom", fill="x")
        ttk.Separator(bottom).pack(fill="x", pady=(6, 6))
        self.start_btn = ttk.Button(bottom, text="▶ 执行任务", command=self._start)
        self.start_btn.pack(fill="x", ipady=6)
        self.stop_btn = ttk.Button(bottom, text="■ 结束任务", command=self._stop, state="disabled")
        self.stop_btn.pack(fill="x", ipady=6, pady=6)
        self.status_var = tk.StringVar(value="空闲")
        ttk.Label(bottom, textvariable=self.status_var, foreground="#0a6").pack(anchor="w")

        row = ttk.Frame(bottom)
        row.pack(fill="x", pady=(8, 0))
        self.runs_label = ttk.Label(row, text="目标次数")
        self.runs_label.pack(side="left")
        self.runs_var = tk.StringVar(value="300")
        self.runs_entry = ttk.Entry(row, textvariable=self.runs_var, width=8)
        self.runs_entry.pack(side="right")

        row2 = ttk.Frame(bottom)
        row2.pack(fill="x", pady=6)
        ttk.Label(row2, text="截图模式").pack(side="left")
        self.mode_var = tk.StringVar(value="color")
        ttk.Combobox(row2, textvariable=self.mode_var, width=8, state="readonly",
                     values=["color", "raw"]).pack(side="right")

        # ---- 上面留给任务列表和说明 ----
        top = ttk.Frame(left)
        top.pack(side="top", fill="both", expand=True)
        ttk.Label(top, text="任务列表", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
        self.lb = tk.Listbox(top, height=6, font=("Microsoft YaHei UI", 10),
                             activestyle="none", exportselection=False)
        self.lb.pack(fill="both", expand=True, pady=(4, 6))
        self.lb.bind("<<ListboxSelect>>", lambda e: self._on_select())

        ttk.Button(top, text="刷新任务列表", command=self._reload_tasks).pack(fill="x")
        ttk.Separator(top).pack(fill="x", pady=8)
        self.desc_var = tk.StringVar(value="（选一个任务看说明）")
        ttk.Label(top, textvariable=self.desc_var, wraplength=280,
                  justify="left", foreground="#444").pack(anchor="w", fill="x")

        # ---------- 右侧 ----------
        right = ttk.Frame(outer)
        right.pack(side="left", fill="both", expand=True)

        head = ttk.Frame(right)
        head.pack(fill="x")
        self.progress_var = tk.StringVar(value="尚未开始")
        ttk.Label(head, textvariable=self.progress_var,
                  font=("Microsoft YaHei UI", 13, "bold")).pack(side="left")
        ttk.Button(head, text="清空日志", command=self._clear_log).pack(side="right")
        self.autoscroll = tk.BooleanVar(value=True)
        ttk.Checkbutton(head, text="自动滚动", variable=self.autoscroll).pack(side="right", padx=8)

        box = ttk.Frame(right)
        box.pack(fill="both", expand=True, pady=(6, 0))
        self.txt = tk.Text(box, wrap="none", font=("Consolas", 9), bg="#111", fg="#ddd",
                           insertbackground="#ddd")
        sb = ttk.Scrollbar(box, command=self.txt.yview)
        self.txt.configure(yscrollcommand=sb.set)
        self.txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.txt.tag_configure("err", foreground="#ff6b6b")
        self.txt.tag_configure("ok", foreground="#5ee08a")
        self.txt.tag_configure("info", foreground="#7cc7ff")

    # ================= 任务列表 =================
    def _reload_tasks(self):
        self.lb.delete(0, "end")
        self.tasks = core.discover()
        if not self.tasks:
            self.lb.insert("end", "（tasks/ 下没有找到任务）")
            self.current = None
            return
        for name, cls in self.tasks:
            self.lb.insert("end", f"  {getattr(cls, 'name', name)}")
        self.lb.selection_set(0)
        self._on_select()

    def _on_select(self):
        sel = self.lb.curselection()
        if not sel or not self.tasks:
            return
        idx = sel[0]
        if idx >= len(self.tasks):
            return
        name, cls = self.tasks[idx]
        self.current = cls
        self.desc_var.set(f"{getattr(cls, 'desc', '')}\n\n目录：tasks/{name}/")
        if getattr(cls, "supports_runs", True):
            self.runs_entry.configure(state="normal")
            self.runs_label.configure(foreground="#000")
        else:
            self.runs_entry.configure(state="disabled")
            self.runs_label.configure(foreground="#999")

    # ================= 执行 / 结束 =================
    def _start(self):
        if self.runner.running:
            messagebox.showinfo(APP_TITLE, "已有任务在运行，先结束它。")
            return
        if self.current is None:
            messagebox.showwarning(APP_TITLE, "先选一个任务。")
            return
        try:
            runs = int(self.runs_var.get().strip() or 0)
        except ValueError:
            messagebox.showwarning(APP_TITLE, "目标次数得是数字（0 = 不限）。")
            return
        task = self.current()
        ok, err = self.runner.start(task, target_runs=runs, shot_mode=self.mode_var.get())
        if not ok:
            messagebox.showwarning(APP_TITLE, err)
            return
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_var.set("运行中…")
        self.progress_var.set("准备中…")

    def _stop(self):
        self.runner.stop()
        self.status_var.set("正在停止…")
        self.stop_btn.configure(state="disabled")

    def _clear_log(self):
        self.txt.delete("1.0", "end")
        self.log_lines = 0

    # ================= 日志刷新 =================
    def _append(self, text, tag=None):
        self.txt.insert("end", text + "\n", tag or "")
        self.log_lines += 1
        if self.log_lines > MAX_LOG_LINES:
            self.txt.delete("1.0", "200.0")
            self.log_lines -= 200
        if self.autoscroll.get():
            self.txt.see("end")

    def _tick(self):
        for kind, payload in self.runner.poll():
            if kind == "log":
                tag = "err" if "!!" in payload else ("ok" if "完成" in payload else None)
                self._append(payload, tag)
            elif kind == "progress":
                step, total, note = payload
                if total:
                    self.progress_var.set(f"{note or '进度'} ({step}/{total})")
                else:
                    self.progress_var.set(note or "运行中…")
            elif kind == "done":
                self._append(f"—— {payload} ——", "info")
                self.status_var.set("空闲")
                self.progress_var.set(payload)
                self.start_btn.configure(state="normal")
                self.stop_btn.configure(state="disabled")
        # 运行状态兜底（比如线程异常退出）
        if not self.runner.running and self.stop_btn["state"] == "normal":
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.status_var.set("空闲")
        self.root.after(120, self._tick)


def _selftest():
    """自检：不显示界面，只检查关键模块能否加载、模板是否打包进去。

    用途：打包成 windowed exe 后，出错是没有任何提示的，必须有个自检入口。
    结果写到 exe/脚本同目录的 selftest.log。
    """
    import traceback
    lines = []
    ok = True

    def rec(msg):
        lines.append(str(msg))
        print(msg, flush=True)

    rec(f"frozen={getattr(sys, 'frozen', False)}")
    rec(f"app_root={APP_ROOT}")
    try:
        from core.paths import res_root, app_path
        rr = res_root()
        rec(f"res_root={rr}")
        rec(f"res_root 存在={os.path.isdir(rr)}")
        if os.path.isdir(rr):
            rec("res_root 内容: " + ", ".join(sorted(os.listdir(rr))[:20]))
    except Exception as e:
        ok = False
        rec(f"!! core.paths 失败: {e}")
        rec(traceback.format_exc())

    # 各模块
    for mod in ("adbkit", "vision", "human_click", "ascii_out", "core.tasks",
                "core.runner", "core.nav", "core.popup_watch"):
        try:
            __import__(mod)
            rec(f"import {mod} OK")
        except Exception as e:
            ok = False
            rec(f"!! import {mod} 失败: {e}")

    # 任务发现 + 模板
    try:
        import core
        tasks = core.discover()
        rec(f"发现任务 {len(tasks)} 个: {[n for n, _ in tasks]}")
        if not tasks:
            ok = False
            rec("!! 一个任务都没发现（tasks/ 没打包进去？）")
        # 抽查模板
        from tasks.jiejie_tupo import ui as jui
        from tasks.event_dungeon import game as eg
        for label, p in (("结界-入口模板", jui.tpl("t_jj_entry_bottom.png")),
                         ("结界-庭院栏", jui.tpl("t_courtyard_bar.png")),
                         ("活动-挑战键", eg.tpl("t_challenge.png")),
                         ("活动-次数0", eg.tpl("t_count_zero.png"))):
            exist = os.path.exists(p)
            rec(f"{label}: {'OK' if exist else '!! 缺失'}  {p}")
            if not exist:
                ok = False
    except Exception as e:
        ok = False
        rec(f"!! 任务/模板检查失败: {e}")
        rec(traceback.format_exc())

    # tkinter
    try:
        import tkinter
        r = tkinter.Tk()
        r.withdraw()
        r.destroy()
        rec("tkinter 可用 OK")
    except Exception as e:
        ok = False
        rec(f"!! tkinter 失败: {e}")

    rec("自检结果: " + ("全部通过" if ok else "有失败项"))
    try:
        with open(os.path.join(APP_ROOT, "selftest.log"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception:
        pass
    return 0 if ok else 1


def main():
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    root = tk.Tk()
    try:
        root.call("tk", "scaling", 1.25)
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
