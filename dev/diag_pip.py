# -*- coding: utf-8 -*-
"""诊断 pip：装个极小的包试试，并试几种参数组合。"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(HERE, "build_tmp")
os.makedirs(TMP, exist_ok=True)

env = dict(os.environ)
env["TMP"] = TMP
env["TEMP"] = TMP
env["NO_PROXY"] = "*"

attempts = [
    ("普通 --user", ["--user"]),
    ("--no-cache-dir", ["--user", "--no-cache-dir"]),
    ("指定 --target", ["--target", os.path.join(TMP, "pkgs"), "--no-cache-dir"]),
]
for label, extra in attempts:
    cmd = [sys.executable, "-m", "pip", "install", "--no-input",
           "--disable-pip-version-check"] + extra + ["six"]
    print(f"\n=== {label} ===", flush=True)
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    out = (p.stdout or "") + (p.stderr or "")
    for line in out.splitlines():
        if any(k in line for k in ("Successfully", "ERROR", "error:", "Permission",
                                   "already satisfied", "Installing")):
            print("   ", line.strip()[:160])
    print("    返回码:", p.returncode)
