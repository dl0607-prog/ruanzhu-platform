"""Windows 便携版启动器（PyInstaller 打包入口）。

双击运行：自动挑选空闲端口、启动后端、用默认浏览器打开。
关闭黑色控制台窗口即退出服务；数据保存在 exe 同目录的 data/ 文件夹。
"""
import multiprocessing
import socket
import sys
import threading
import webbrowser
from pathlib import Path

# 便携版（Windows 嵌入式 Python 随包分发）:数据/导出目录跟随 exe 所在文件夹
_EXE_DIR = Path(sys.executable).resolve().parent
if (_EXE_DIR / "python311._pth").exists() and not getattr(sys, "frozen", False):
    sys.frozen = True

import uvicorn

from backend.app.main import app

HOST = "127.0.0.1"
DEFAULT_PORT = 8310


def _find_port() -> int:
    for port in range(DEFAULT_PORT, DEFAULT_PORT + 10):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((HOST, port))
                return port
            except OSError:
                continue
    return DEFAULT_PORT


def _open_browser_later(port: int) -> None:
    threading.Timer(1.2, lambda: webbrowser.open(f"http://{HOST}:{port}")).start()


def main() -> None:
    port = _find_port()
    print("软著工场 · 软著申请辅助平台")
    print(f"服务已启动：http://{HOST}:{port}（稍后会自动打开浏览器）")
    print("关闭本窗口即退出服务；数据保存在本程序同目录的 data 文件夹。")
    _open_browser_later(port)
    # loop="asyncio"：Windows 打包环境下避免 uvloop 依赖
    uvicorn.run(app, host=HOST, port=port, loop="asyncio", log_level="warning")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
