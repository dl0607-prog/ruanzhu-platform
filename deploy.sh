#!/usr/bin/env bash
# ============================================================
# 软著工场 · 云服务器一键部署脚本
# 适用:腾讯云轻量应用服务器 / CVM(Ubuntu、Debian、CentOS、TencentOS)
# 用法(在【服务器网页终端】里粘贴,不要在 Mac/Windows 本机终端运行):
#   curl -fsSL https://raw.githubusercontent.com/dl0607-prog/ruanzhu-platform/main/deploy.sh -o /tmp/rz.sh && bash /tmp/rz.sh
# 部署完成后浏览器访问 http://<服务器公网IP> 即可。
# ============================================================

# 防呆:如果在本机 macOS 上运行,直接提示退出(避免装错机器)
if [ "$(uname)" = "Darwin" ]; then
  echo "⚠️ 检测到这是 Mac 电脑,不是云服务器。"
  echo "请回到浏览器里的轻量服务器控制台 → 点服务器卡片上的「登录」,"
  echo "在弹出的【网页终端】窗口中粘贴本命令。"
  exit 1
fi

set -e

# 需要 root 权限(不是 root 时自动提权)
if [ "$(id -u)" != "0" ]; then
  echo "需要管理员权限,正在提权…"
  exec sudo bash "$0"
fi

echo "==> [1/4] 检查 Python3 环境"
if ! command -v python3 >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq && apt-get install -y -qq python3 python3-venv python3-pip
  elif command -v yum >/dev/null 2>&1; then
    yum install -y -q python3 python3-pip
  fi
fi
# 确保 venv 模块可用(Debian/Ubuntu 需要单独装 python3-venv)
if ! python3 -m venv --help >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    apt-get install -y -qq python3-venv python3-pip
  fi
fi
python3 --version

echo "==> [2/4] 下载最新版项目代码"
mkdir -p /opt && cd /opt
# 备份已有数据(重复部署/升级时保护项目数据不丢失)
BACKUP=/tmp/rz-data-backup
rm -rf "$BACKUP" && mkdir -p "$BACKUP"
if [ -d ruanzhu-platform-main/data ]; then cp -a ruanzhu-platform-main/data "$BACKUP/"; fi
if [ -d ruanzhu-platform-main/exports ]; then cp -a ruanzhu-platform-main/exports "$BACKUP/"; fi
curl -fL --retry 3 --retry-delay 2 -o ruanzhu.tar.gz \
  https://github.com/dl0607-prog/ruanzhu-platform/archive/refs/heads/main.tar.gz
rm -rf ruanzhu-platform-main
tar xzf ruanzhu.tar.gz
cd ruanzhu-platform-main
# 还原数据
if [ -d "$BACKUP/data" ]; then cp -a "$BACKUP/data" ./data; echo "已恢复历史数据 data/"; fi
if [ -d "$BACKUP/exports" ]; then cp -a "$BACKUP/exports" ./exports; fi
[ -f .env ] || cp .env.example .env

echo "==> [3/4] 安装依赖(清华镜像源,约 1-2 分钟)"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
.venv/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r backend/requirements.txt

echo "==> [4/4] 注册开机自启服务并启动"
# 80 端口转发到 8310:防火墙放行 80 或 8310 任意一个都能访问
cat > /etc/systemd/system/ruanzhu.service <<'UNIT'
[Unit]
Description=Ruanzhu Workshop (软著工场)
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/ruanzhu-platform-main/backend
ExecStartPre=/bin/bash -c 'iptables -t nat -D PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8310 2>/dev/null; iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8310 || true'
ExecStart=/opt/ruanzhu-platform-main/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8310
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now ruanzhu

echo ""
echo "==> 等待服务就绪…"
ready=0
for i in $(seq 1 40); do
  if curl -sf http://127.0.0.1:8310/api/health >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 3
done

echo ""
if [ "$ready" = "1" ]; then
  echo "✅ 部署成功!"
  IP=$(curl -s --max-time 3 http://metadata.tencentyun.com/latest/meta-data/public-ipv4 2>/dev/null || true)
  if [ -n "$IP" ]; then
    echo "🌐 系统地址(发给任何人即可用): http://$IP"
  else
    echo "🌐 系统地址: http://<这台服务器的公网IP>(在控制台可查看)"
  fi
  echo ""
  echo "提示:如果浏览器打不开,请到服务器控制台的「防火墙」页面,"
  echo "      放行 TCP 端口 80 和 8310(各添加一条规则),再访问即可。"
else
  echo "⚠️ 服务尚未就绪,请运行以下命令查看日志:"
  echo "    journalctl -u ruanzhu -n 100 --no-pager"
fi
