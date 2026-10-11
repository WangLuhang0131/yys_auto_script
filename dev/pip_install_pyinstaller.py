# -*- coding: utf-8 -*-
"""用 Python 直接跑 pip 安装（避开 PowerShell 传参/管道问题），输出写文件。"""
import subprocess
import sys
import os

PY = sys.executable
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pip_install.log")

cmd = [PY, "-m", "pip", "install", "--no-input", "--disable-pip-version-check",
       "--user", "pyinstaller"]
print("执行:", " ".join(cmd), flush=True)
with open(LOG, "w", encoding="utf-8") as f:
    p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, text=True)
print("返回码:", p.returncode, flush=True)
with open(LOG, encoding="utf-8", errors="replace") as f:
    lines = f.read().splitlines()
print("\n".join(lines[-15:]))
