# -*- coding: utf-8 -*-
"""不依赖 pip 的 wheel 解包步骤：下载 wheel 后用 Python 直接解压到 .pydist/。

背景：这台机器上 pip 的 --target / 解包步骤会报 Permission denied（沙箱所致），
但 pip download 能正常把 wheel 下下来。所以：
  pip download -> zipfile 解压 -> 放进 .pydist/
程序启动时（core/paths.py）会把 .pydist 挂到 sys.path 上。
"""
import glob
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DL = os.path.join(HERE, "build_tmp", "wheels")
DEST = os.path.join(HERE, ".pydist")
os.makedirs(DL, exist_ok=True)
os.makedirs(DEST, exist_ok=True)

env = dict(os.environ)
env["TMP"] = os.path.join(HERE, "build_tmp")
env["TEMP"] = env["TMP"]
env["NO_PROXY"] = "*"

PKGS = ["pyinstaller"]        # 需要什么就加什么，依赖会自动带上
print("下载 wheel 到", DL, flush=True)
cmd = [sys.executable, "-m", "pip", "download", "--no-input", "--no-deps",
       "--disable-pip-version-check", "--dest", DL] + PKGS
p = subprocess.run(cmd, capture_output=True, text=True, env=env)
print((p.stdout or "")[-800:], flush=True)
if p.returncode != 0:
    print("!! 下载失败：", (p.stderr or "")[-500:])
    sys.exit(1)

# pyinstaller 的依赖也要下（--no-deps 之外单独列）
DEPS = ["altgraph", "packaging", "pefile", "pywin32-ctypes", "pyinstaller-hooks-contrib",
        "setuptools"]
cmd2 = [sys.executable, "-m", "pip", "download", "--no-input", "--no-deps",
        "--disable-pip-version-check", "--dest", DL] + DEPS
p2 = subprocess.run(cmd2, capture_output=True, text=True, env=env)
print((p2.stdout or "")[-1200:], flush=True)

wheels = sorted(glob.glob(os.path.join(DL, "*.whl")))
print(f"\n共 {len(wheels)} 个 wheel，开始解压到 {DEST}", flush=True)
for w in wheels:
    name = os.path.basename(w)
    try:
        with zipfile.ZipFile(w) as z:
            z.extractall(DEST)
        print("  +", name, flush=True)
    except Exception as e:
        print("  !! 失败", name, e, flush=True)

print("\n解压完成。检查关键模块：")
for mod in ("PyInstaller", "altgraph", "pefile", "packaging", "setuptools"):
    hit = glob.glob(os.path.join(DEST, mod + "*"))
    print(f"  {mod:26s} {'OK' if hit else '缺失'}")
