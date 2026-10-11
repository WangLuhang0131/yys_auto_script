# -*- coding: utf-8 -*-
"""对比：单线程截图 vs 与看门狗并发截图，谁的失败率高。"""
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adbkit import Adb                                   # noqa: E402
from humanize import Human                               # noqa: E402
from core.popup_watch import PopupWatcher                # noqa: E402

a = Adb()


def bench(tag, n=8, concurrent=False):
    ok = fail = 0
    w = None
    h = Human(a, log=lambda m: None)
    if concurrent:
        w = PopupWatcher(a, h, lambda m: None, poll=1.0)
        w.start()
    t0 = time.time()
    for i in range(n):
        try:
            a.screenshot()
            ok += 1
        except Exception as e:
            fail += 1
            print(f"   失败: {type(e).__name__}")
        time.sleep(0.3)
    if w:
        w.stop()
    dt = time.time() - t0
    print(f"{tag}: 成功 {ok} 失败 {fail}  用时 {dt:.1f}s")


print("=== 单线程 ===")
bench("单线程", 8, concurrent=False)
print("\n=== 与看门狗并发 ===")
bench("并发", 8, concurrent=True)
