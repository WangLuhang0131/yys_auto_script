# -*- coding: utf-8 -*-
"""公共：程序根目录 / 资源目录。

为什么要单独一个文件：
  1. 打包成 exe 后，代码不在原来的目录结构里，`__file__` 指向临时解包目录；
  2. 双击 exe 时"当前工作目录"可能是任意目录，不能靠 os.getcwd()。
所以统一走这里的函数：
  · app_root()  —— 可写目录（放 logs/、shots/），exe 时是 exe 所在目录
  · res_root()  —— 只读资源目录（templates/），exe 时是 PyInstaller 解包目录
"""
from __future__ import annotations

import os
import sys


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def app_root() -> str:
    """可写根目录：日志、截图都放这里。"""
    if is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def res_root() -> str:
    """只读资源根目录：找 templates/ 之类的文件。"""
    if is_frozen():
        # PyInstaller 单文件模式解包到 sys._MEIPASS
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def res_path(*parts: str) -> str:
    return os.path.join(res_root(), *parts)


def app_path(*parts: str) -> str:
    return os.path.join(app_root(), *parts)


def ensure_app_dirs():
    """保证可写目录存在（logs 等）。"""
    for sub in ("logs",):
        try:
            os.makedirs(app_path(sub), exist_ok=True)
        except Exception:
            pass


def add_local_pydist():
    """把项目自带的 .pydist 目录挂到 sys.path（打包工具等第三方库放在那里）。

    背景：这台机器上 pip 的解包步骤会被沙箱拒绝，所以第三方库是用
    tools/fetch_wheels_manual.py 直接下 wheel、解压到 .pydist/ 的。
    正常用户用 pip install 装依赖时，这个目录不存在，函数什么也不做。
    """
    p = app_path(".pydist")
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)


# 模块导入时自动挂上，方便任何入口都能用
add_local_pydist()
