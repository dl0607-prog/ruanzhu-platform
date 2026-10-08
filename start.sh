#!/bin/bash
# 软著工场一键启动脚本
set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "[1/3] 创建虚拟环境…"
  python3 -m venv .venv
  .venv/bin/pip install -q -r backend/requirements.txt
else
  echo "[1/3] 虚拟环境已就绪"
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "[2/3] 已生成 .env；请先设置至少12位 ADMIN_PASSWORD，本机HTTP还需 COOKIE_SECURE=false"
else
  echo "[2/3] .env 已存在"
fi

echo "[3/3] 启动服务：本机 http://localhost:8310（局域网设备可用 http://本机IP:8310）"
cd backend
exec ../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8310
