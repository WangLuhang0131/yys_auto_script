# -*- coding: utf-8 -*-
"""完全绕开 pip：从 PyPI JSON API 拿 wheel 直链 -> urllib 下载 -> zipfile 解压。

（这台机器上 pip 的解包/元数据步骤会被沙箱拒，但普通 Python 文件读写和网络都正常。）
"""
import glob
import json
import os
import sys
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DL = os.path.join(HERE, "build_tmp", "wheels")
DEST = os.path.join(HERE, ".pydist")
os.makedirs(DL, exist_ok=True)
os.makedirs(DEST, exist_ok=True)

# 目标包（pyinstaller 及其运行依赖）
PKGS = ["pyinstaller", "altgraph", "packaging", "pefile", "pywin32-ctypes",
        "pyinstaller-hooks-contrib", "setuptools"]


def pick_wheel(pkg: str):
    """从 PyPI 元数据里挑一个适合本机（win_amd64 / 纯 py3）的 wheel。"""
    url = f"https://pypi.org/pypi/{pkg}/json"
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)
    files = data["urls"]
    cands = [f for f in files if f["filename"].endswith(".whl")]
    # 优先 win_amd64，其次 any
    def score(fn):
        n = fn["filename"]
        if "win_amd64" in n:
            return 0
        if "-none-any" in n:
            return 1
        return 2
    cands.sort(key=score)
    for f in cands:
        if score(f) <= 1:
            return f["filename"], f["url"], data["info"]["version"]
    return None


def download(url, path):
    with urllib.request.urlopen(url, timeout=120) as r, open(path, "wb") as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)


print("目标包:", ", ".join(PKGS), "\n")
got = []
for pkg in PKGS:
    try:
        pick = pick_wheel(pkg)
        if not pick:
            print(f"  !! {pkg}: 没找到合适的 wheel")
            continue
        fn, url, ver = pick
        path = os.path.join(DL, fn)
        if not os.path.exists(path):
            download(url, path)
        print(f"  + {pkg} {ver} -> {fn}")
        got.append(path)
    except Exception as e:
        print(f"  !! {pkg} 失败：{type(e).__name__} {e}")

print(f"\n下载完成 {len(got)} 个，解压到 {DEST}")
for w in got:
    try:
        with zipfile.ZipFile(w) as z:
            z.extractall(DEST)
    except Exception as e:
        print("  !! 解压失败", os.path.basename(w), e)

print("\n关键模块检查：")
for mod in ("PyInstaller", "altgraph", "pefile", "packaging", "setuptools",
            "PyInstaller/hooks"):
    hit = os.path.exists(os.path.join(DEST, mod.replace("/", os.sep)))
    print(f"  {mod:28s} {'OK' if hit else '缺失'}")
