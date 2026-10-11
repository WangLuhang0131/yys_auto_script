# -*- coding: utf-8 -*-
"""把 pip 的临时目录指到工作区内，绕开沙箱对系统 Temp 的写限制。"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(HERE, "build_tmp")
os.makedirs(TMP, exist_ok=True)
LOG = os.path.join(HERE, "build_tmp", "pip.log")

env = dict(os.environ)
env["TMP"] = TMP
env["TEMP"] = TMP
env["TMPDIR"] = TMP
env["NO_PROXY"] = "*"
env["no_proxy"] = "*"

cmd = [sys.executable, "-m", "pip", "install", "--no-input",
       "--disable-pip-version-check", "--cache-dir", os.path.join(TMP, "pipcache"),
       "pyinstaller"]
print("执行:", " ".join(cmd), flush=True)
print("TMP ->", TMP, flush=True)
with open(LOG, "w", encoding="utf-8") as f:
    p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, text=True, env=env)
print("返回码:", p.returncode, flush=True)
with open(LOG, encoding="utf-8", errors="replace") as f:
    lines = f.read().splitlines()
print("\n".join(lines[-12:]))
