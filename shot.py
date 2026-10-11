# -*- coding: utf-8 -*-
"""采集器：按名称保存当前游戏画面，便于提取识别模板。
用法: python shot.py <name>
"""
import sys, os
from adbkit import Adb

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "shot"
    a = Adb()
    img = a.screenshot()
    os.makedirs("shots", exist_ok=True)
    path = os.path.join("shots", name + ".png")
    img.save(path)
    print("saved", path, img.size)
