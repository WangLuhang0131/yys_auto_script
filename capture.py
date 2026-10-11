# -*- coding: utf-8 -*-
"""抓一张 MuMu 模拟器当前画面，保存为 PNG。"""
import subprocess, sys, os

ADB = r"E:\MuMuPlayer\nx_main\adb.exe"
SERIAL = "emulator-5554"
OUT = sys.argv[1] if len(sys.argv) > 1 else "shots/cap.png"

def adb(*args, binary=False):
    cmd = [ADB, "-s", SERIAL] + list(args)
    r = subprocess.run(cmd, capture_output=True)
    if binary:
        return r.stdout
    return r.stdout.decode("utf-8", "replace").strip(), r.returncode

if __name__ == "__main__":
    r = subprocess.run([ADB, "-s", SERIAL, "exec-out", "screencap", "-p"], capture_output=True)
    print("rc:", r.returncode, "out:", len(r.stdout), "err:", r.stderr[:400])
    data = r.stdout
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(data)
    print("bytes:", len(data))
    size, _ = adb("shell", "wm", "size")
    print("wm size:", size)
    # PNG IHDR
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        import struct
        w, h = struct.unpack(">II", data[16:24])
        print("png:", w, "x", h)
    else:
        print("header:", data[:8])
