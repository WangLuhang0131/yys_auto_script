# -*- coding: utf-8 -*-
"""任务基类与任务发现。

规矩：
- 每个任务住在 tasks/<目录名>/，入口固定是 tasks/<目录名>/task.py 里的 `Task` 类。
- 任务之间互不 import、互不继承；公共能力只从 core/ 和根目录工具拿。
- 因此删除任意任务目录，其余任务与 GUI 都不受影响（GUI 靠扫描目录发现任务）。
"""
from __future__ import annotations

import importlib
import os
import pkgutil
import threading
import time
import traceback


# ============================================================
# 运行上下文（任务拿到它就能干活）
# ============================================================
class TaskContext:
    def __init__(self, adb, human, log, should_stop, progress=None,
                 target_runs: int = 0, settings: dict | None = None):
        self.a = adb                      # Adb 实例
        self.human = human                # 拟人化点击层
        self.log = log                    # log(msg) 写日志（GUI 右边 + 文件）
        self.should_stop = should_stop    # () -> bool
        self.progress = progress or (lambda step, total, note="": None)
        self.target_runs = int(target_runs or 0)   # 0 = 不限
        self.settings = settings or {}
        self.state = {}
        self._t0 = time.time()

    # ---------- 便捷 ----------
    def elapsed(self) -> float:
        return time.time() - self._t0

    def stopped(self) -> bool:
        return bool(self.should_stop())

    def set_progress(self, step: int, total: int, note: str = ""):
        """上报进度，GUI 会显示成 战斗(3/9) 这种。"""
        self.progress(step, total, note)

    def sleep(self, sec: float):
        """可被停止打断的等待。"""
        end = time.time() + sec
        while time.time() < end:
            if self.stopped():
                return
            time.sleep(min(0.1, max(0.0, end - time.time())))

    def wait_until(self, fn, timeout=30.0, interval=0.3, desc=""):
        """轮询 fn() 直到为真；返回 True/False。可被停止打断。"""
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.stopped():
                return False
            try:
                if fn():
                    return True
            except Exception:
                pass
            time.sleep(interval)
        if desc:
            self.log(f"  !! 等待超时：{desc}")
        return False


# ============================================================
# 任务基类
# ============================================================
class TaskBase:
    #: 显示名（GUI 左侧列表）
    name = "未命名任务"
    #: 日志文件名用的短名（ASCII）。留空则用 name 的 ASCII 化结果
    slug = ""
    #: 一行说明
    desc = ""
    #: 是否支持「刷多少次」
    supports_runs = True
    #: 是否需要彩色截图（默认 True，判据更准；纯速度型任务可设 False）
    need_color = True
    #: 任务结束后是否自动回庭院（默认 True）
    return_home = True

    def __init__(self):
        self._stop = threading.Event()

    # ---------- 生命周期 ----------
    def request_stop(self):
        self._stop.set()

    def is_stopping(self) -> bool:
        return self._stop.is_set()

    # ---------- 子类必须实现 ----------
    def run(self, ctx: TaskContext):
        """任务主体。用 ctx.log 输出，用 ctx.stopped() 判断退出。"""
        raise NotImplementedError

    # ---------- 可选 ----------
    def check_ready(self, ctx: TaskContext):
        """执行前检查（游戏是否在能识别的页面）。返回 (可否开始, 提示文字)。"""
        return True, ""

    def requirements(self) -> str:
        """给界面显示的前置条件说明（可选）。"""
        return ""


# ============================================================
# 任务发现
# ============================================================
def _tasks_dir() -> str:
    """tasks/ 目录（打包成 exe 后在解包目录里）。"""
    try:
        from core.paths import res_root
        root = res_root()
    except Exception:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "tasks")


def discover():
    """扫描 tasks/ 下所有任务，返回 [(目录名, Task 类)]。
    任何一个任务坏掉只会被跳过（并打印原因），不影响其它任务。"""
    result = []
    root = _tasks_dir()
    if not os.path.isdir(root):
        return result
    for m in sorted(pkgutil.iter_modules([root])):
        name = m.name
        if name.startswith("_") or name == "base":
            continue
        try:
            sub = importlib.import_module(f"tasks.{name}.task")
            cls = getattr(sub, "Task", None)
            if cls is None:
                print(f"[tasks] {name}: task.py 里没有 Task 类，已跳过")
                continue
            result.append((name, cls))
        except Exception as e:
            print(f"[tasks] {name} 加载失败：{e}")
            traceback.print_exc()
    return result


def load_task(name: str):
    """按目录名加载单个任务类。"""
    for n, cls in discover():
        if n == name:
            return cls
    return None
