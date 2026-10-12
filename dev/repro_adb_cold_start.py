# -*- coding: utf-8 -*-
"""复现并诊断：重启后 adb 服务/设备未就绪时，screencap 会怎样失败。

场景：刚开机 -> adb 服务没跑 / 设备还在连 -> 脚本第一次截图就炸。
"""
import subprocess
import sys
import time

sys.path.insert(0, r"D:\Program Files\WKSPC\yys")

ADB = r"E:\MuMuPlayer\nx_main\adb.exe"


def run(args, timeout=40):
    p = subprocess.run([ADB] + args, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


print("=== 1) 杀掉 adb 服务，模拟刚重启 ===")
print(run(["kill-server"]))
time.sleep(1)

print("\n=== 2) 立刻探设备（服务没起来时会失败）===")
rc, out, err = run(["devices"])
print("  rc=%s out=%r err=%r" % (rc, out, err))

print("\n=== 3) 立刻截图（复现报错）===")
t0 = time.time()
p = subprocess.run([ADB, "-s", "emulator-5554", "exec-out", "screencap", "-p"],
                   capture_output=True, timeout=60)
print("  字节数 %d  用时 %.1fs  返回码 %s" % (len(p.stdout), time.time() - t0, p.returncode))
print("  stderr:", p.stderr.decode("utf-8", "replace").strip()[:200])
if p.stdout[:8] != b"\x89PNG\r\n\x1a\n":
    print("  -> 不是 PNG！头部:", p.stdout[:40])

print("\n=== 4) 等几秒再试（看要多久才恢复）===")
for i in range(6):
    time.sleep(2)
    p = subprocess.run([ADB, "-s", "emulator-5554", "exec-out", "screencap", "-p"],
                       capture_output=True, timeout=60)
    ok = p.stdout[:8] == b"\x89PNG\r\n\x1a\n"
    print("  +%2ds 字节 %7d  是PNG=%s  stderr=%s"
          % ((i + 1) * 2, len(p.stdout), ok,
             p.stderr.decode("utf-8", "replace").strip()[:80]))
    if ok:
        break

print("\n=== 5) 现在 devices 状态 ===")
print(run(["devices"]))
