# -*- coding: utf-8 -*-
"""把控制台打包成单个 exe（PyInstaller）。

要点：
  · 单文件（--onefile）+ 无控制台窗口（--windowed）
  · tasks/ 整个目录打进包里（模板、各任务的代码都靠它）
  · 关键模块显式声明（PyInstaller 的静态分析对 tkinter/numpy/PIL 有时会漏）
  · exe 放在 release/ 目录，双击即用

注意：本机 pip 的解包步骤被沙箱拒绝，所以 PyInstaller 是用
tools/fetch_wheels_manual.py 直接下 wheel 解压到 .pydist/ 的；
core/paths.py 启动时会把它挂到 sys.path。
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 项目根（tools 的上一级）
DIST = os.path.join(HERE, "release")
WORK = os.path.join(HERE, "build_tmp", "pyinstaller")

# 保证能找到 .pydist 里的 PyInstaller
sys.path.insert(0, os.path.join(HERE, ".pydist"))
sys.path.insert(0, HERE)
print("项目根:", HERE, flush=True)
print(".pydist 存在:", os.path.isdir(os.path.join(HERE, ".pydist")), flush=True)

CMD = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm", "--clean",
    # 默认单文件；--onedir 打成文件夹（不往 Temp 解包，某些受限环境下更稳）
    "--onedir" if "--onedir" in sys.argv else "--onefile",
    # GUI 程序默认不要黑窗口；打控制台调试版时用 --console 覆盖
    "--windowed" if "--console" not in sys.argv else "--console",
    "--name", os.environ.get("YYS_EXE_NAME", "阴阳师脚本控制台"),
    "--distpath", DIST,
    "--workpath", WORK,
    "--specpath", WORK,
    # 把任务目录（含模板）打进包：exe 里靠 res_root() 定位
    "--add-data", f"{os.path.join(HERE, 'tasks')}{os.pathsep}tasks",
    # 显式声明（静态分析容易漏的）
    "--hidden-import", "tasks.event_dungeon.task",
    "--hidden-import", "tasks.event_dungeon.game",
    "--hidden-import", "tasks.jiejie_tupo.task",
    "--hidden-import", "tasks.jiejie_tupo.attack",
    "--hidden-import", "tasks.jiejie_tupo.ui",
    "--hidden-import", "core.tasks",
    "--hidden-import", "core.runner",
    "--hidden-import", "core.nav",
    "--hidden-import", "core.popup_watch",
    "--hidden-import", "core.paths",
    "--hidden-import", "vision",
    "--hidden-import", "adbkit",
    "--hidden-import", "human_click",
    "--hidden-import", "ascii_out",
    "--hidden-import", "PIL._tkinter_finder",
    "--collect-submodules", "PIL",
    os.path.join(HERE, "gui.py"),
]

if __name__ == "__main__":
    os.makedirs(DIST, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    print("打包命令：")
    print("  " + " ".join(CMD))
    print("\n开始打包（可能要几分钟）...\n", flush=True)

    # 关键：子进程不会继承我们改过的 sys.path，
    # 必须通过 PYTHONPATH 把 .pydist 传下去，否则子进程里 "No module named PyInstaller"
    env = dict(os.environ)
    pydist = os.path.join(HERE, ".pydist")
    env["PYTHONPATH"] = pydist + os.pathsep + HERE + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONUNBUFFERED"] = "1"

    p = subprocess.run(CMD, cwd=HERE, env=env)
    print("\n返回码:", p.returncode)
    if p.returncode == 0:
        exe = os.path.join(DIST, "阴阳师脚本控制台.exe")
        if os.path.exists(exe):
            size = os.path.getsize(exe) / 1024 / 1024
            print(f"\n打包成功：{exe}  ({size:.1f} MB)")
        else:
            print("返回码是 0，但没找到 exe，检查 release 目录")
            for f in os.listdir(DIST):
                print("   ", f)
    else:
        print("打包失败，看上面的错误。")
