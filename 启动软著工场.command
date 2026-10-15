#!/bin/bash
# 软著工场 Mac 一键启动（双击即可）:重启服务并打开浏览器
cd "$(dirname "$0")"
# 停掉旧实例（含端口被占用的残留进程）
pkill -f "uvicorn app.main:app" 2>/dev/null
sleep 1
( sleep 3; open "http://127.0.0.1:8310" ) &
bash start.sh
