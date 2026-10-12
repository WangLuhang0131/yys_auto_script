# -*- coding: utf-8 -*-
"""任务运行器：在后台线程里跑任务，把日志塞进队列给 GUI 消费。

GUI 只和这个类打交道：start() / stop() / poll()。
"""
from __future__ import annotations

import os
import queue
import threading
import time

from adbkit import Adb
from human_click import Human
from core.tasks import TaskContext


class TaskRunner:
    def __init__(self, logdir="logs"):
        self.q: queue.Queue = queue.Queue()
        self.thread: threading.Thread | None = None
        self.task = None
        self.logdir = logdir
        self._logf = None
        self.logpath = None
        self._stop_flag = threading.Event()
        self._progress = (0, 0, "")

    # ---------------- 对外接口 ----------------
    @property
    def running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def start(self, task, target_runs=0, settings=None, serial=None, shot_mode="color"):
        if self.running:
            return False, "已有任务在运行"
        self._stop_flag.clear()
        self.task = task
        os.makedirs(self.logdir, exist_ok=True)
        # 日志文件名用 ASCII slug（中文名在部分环境下不方便）
        slug = (getattr(task, "slug", "") or "").strip()
        if not slug:
            slug = "".join(c if (c.isascii() and (c.isalnum() or c in "-_")) else "_"
                           for c in getattr(task, "name", "task"))
            slug = "_".join(p for p in slug.split("_") if p) or "task"
        self.logpath = os.path.join(
            self.logdir, time.strftime(f"{slug}_%Y%m%d_%H%M%S.log"))
        self._logf = open(self.logpath, "a", encoding="utf-8")
        self.thread = threading.Thread(
            target=self._run, args=(task, target_runs, settings, serial, shot_mode),
            daemon=True)
        self.thread.start()
        return True, ""

    def stop(self):
        self._stop_flag.set()
        if self.task is not None:
            self.task.request_stop()
        self.q.put(("log", "[停止请求已发出，等待当前动作结束...]"))
        return True

    def poll(self):
        """取出所有待处理消息：('log', text) / ('progress', (s,t,note)) / ('done', text)"""
        out = []
        while True:
            try:
                out.append(self.q.get_nowait())
            except queue.Empty:
                break
        return out

    @property
    def progress(self):
        return self._progress

    # ---------------- 线程主体 ----------------
    def _run(self, task, target_runs, settings, serial, shot_mode):
        name = getattr(task, "name", task.__class__.__name__)

        def log(msg):
            line = f"[{time.strftime('%H:%M:%S')}] {msg}"
            if self._logf:
                self._logf.write(line + "\n")
                self._logf.flush()
            self.q.put(("log", line))

        def progress(step, total, note=""):
            self._progress = (step, total, note)
            self.q.put(("progress", (step, total, note)))

        try:
            adb = Adb(serial=serial, shot_mode=shot_mode) if serial else Adb(shot_mode=shot_mode)
            # 让 adb 层的自愈过程（等设备就绪 / 重启 adb 服务）能显示在界面日志里。
            # 打包成 windowed exe 后没有 stdout，print 会消失，所以必须接到这里。
            import adbkit
            adbkit._DIAG_LOG = log
            # 点击互斥锁：看门狗线程和主任务线程共用，避免同一瞬间两次点击撞在一起
            tap_lock = threading.Lock()
            human = Human(adb, log=log, tap_lock=tap_lock)
            ctx = TaskContext(adb=adb, human=human, log=log,
                              should_stop=lambda: self._stop_flag.is_set()
                              or task.is_stopping(),
                              progress=progress, target_runs=target_runs,
                              settings=settings)
            log(f"=== 任务开始：{name} ===")
            log(f"截图模式：{'彩色(PNG)' if shot_mode == 'color' else '灰度(原始帧)'}"
                f"  目标次数：{target_runs or '不限'}")

            # 开机/重启后 adb 服务和模拟器都要时间起来，先等设备就绪再动手，
            # 免得第一张截图就拿到空包、报个看不懂的 "cannot identify image file"。
            log(f"adb：{adb.adb}  设备：{adb.serial}")
            st = adb.device_state()
            if st != "device":
                # 一定要把**原始输出**打出来：解析后的状态看不出问题在哪，
                # 而"外面能连、脚本里连不上"这类事只能靠原始输出定位。
                log(f"设备当前状态={st}，先等它就绪")
                log(f"    adb devices 原始输出：{adb.devices_text()!r}")
                if not adb.wait_ready(timeout=90, log=log):
                    log("!! 设备一直没就绪。上面那行原始输出就是证据，"
                        "请把它发我；同时确认 MuMu 已启动并进入游戏画面")
                    self.q.put(("done", f"{name} 未开始：设备未就绪"))
                    return
            log(f"adb 设备就绪（{adb.serial}）")

            ok, tip = task.check_ready(ctx)
            if not ok:
                log(f"!! 无法开始：{tip}")
                self.q.put(("done", f"{name} 未开始：{tip}"))
                return
            if tip:
                log(f"检查通过：{tip}")

            # 干扰弹窗（悬赏封印等）会卡住战斗，必须开独立线程一直盯着
            watcher = None
            try:
                from core.popup_watch import PopupWatcher
                watcher = PopupWatcher(adb, human, log, tap_lock=tap_lock)
                watcher.start()
                log("干扰弹窗看门狗已启动（悬赏封印这类卡战斗的弹窗会自动点掉）")
            except Exception as e:
                log(f"!! 看门狗启动失败（不影响主流程）：{e}")

            try:
                task.run(ctx)
            finally:
                if watcher is not None:
                    watcher.stop()
                    if watcher.closed_count:
                        log(f"看门狗本次共关掉 {watcher.closed_count} 个干扰弹窗")

            if ctx.stopped():
                log(f"=== 任务已被手动结束：{name} ===")
                done_msg = f"{name} 已手动结束"
            else:
                log(f"=== 任务完成：{name} ===  用时 {ctx.elapsed()/60:.1f} 分钟")
                done_msg = f"{name} 完成"

            # 收尾：把游戏送回庭院，保证下次启动都在同一个已知状态
            if getattr(task, "return_home", True):
                log("--- 收尾：返回庭院 ---")
                try:
                    from core.nav import Returner
                    r = Returner(adb, human, log)
                    ok_home, steps = r.go_home()
                    log(f"--- {'已回到庭院' if ok_home else '!! 没能回到庭院'}"
                        f"（{steps} 步）---")
                except Exception as e:
                    log(f"!! 回庭院出错：{e}")
            self.q.put(("done", done_msg))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            if self._logf:
                self._logf.write(tb + "\n")
                self._logf.flush()
            self.q.put(("log", f"!! 任务异常：{e}"))
            self.q.put(("log", tb.strip().splitlines()[-1]))
            self.q.put(("done", f"{name} 异常退出：{e}"))
        finally:
            if self._logf:
                self._logf.close()
                self._logf = None
