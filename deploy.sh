#!/usr/bin/env bash
# ============================================================
# 软著工场 · 云服务器一键部署脚本
# 适用:腾讯云轻量应用服务器 / CVM(Ubuntu、Debian、CentOS、TencentOS)
# 用法:
#   curl -fsSL https://raw.githubusercontent.com/dl0607-prog/ruanzhu-platform/main/deploy.sh -o /tmp/rz.sh && bash /tmp/rz.sh
# 部署完成后浏览器访问 http://<服务器公网IP> 即可。
# ============================================================
set -e

# 需要 root 权限(不是 root 时自动提权)
if [ "$(id -u)" != "0" ]; then
  echo "需要管理员权限,正在提权…"
  exec sudo bash "$0"
fi

echo "==> [1/5] 检查并安装 Docker(已安装则跳过)"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL --retry 3 -o /tmp/get-docker.sh https://get.docker.com
  sh /tmp/get-docker.sh --mirror Aliyun
fi
systemctl enable --now docker >/dev/null 2>&1 || service docker start >/dev/null 2>&1 || true

echo "==> [2/5] 配置国内镜像加速(腾讯云内网源,构建更快更稳)"
mkdir -p /etc/docker
if [ ! -f /etc/docker/daemon.json ]; then
  cat > /etc/docker/daemon.json <<'JSON'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.m.daocloud.io"
  ]
}
JSON
  systemctl restart docker >/dev/null 2>&1 || true
fi

echo "==> [3/5] 下载最新版项目代码"
mkdir -p /opt
cd /opt
curl -fL --retry 3 --retry-delay 2 -o ruanzhu.tar.gz \
  https://github.com/dl0607-prog/ruanzhu-platform/archive/refs/heads/main.tar.gz
rm -rf ruanzhu-platform-main
tar xzf ruanzhu.tar.gz
cd ruanzhu-platform-main

echo "==> [4/5] 生成配置(pip 使用清华源加速构建)"
[ -f .env ] || cp .env.example .env
sed -i 's#RUN pip install --no-cache-dir -r requirements.txt#RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt#' Dockerfile

# 同时映射 80 和 8310:防火墙放行任意一个端口都能访问
cat > docker-compose.override.yml <<'YAML'
services:
  ruanzhu:
    ports:
      - "80:8310"
      - "8310:8310"
YAML

echo "==> [5/5] 构建并启动(首次约 2-5 分钟,请耐心等待)"
docker compose up -d --build

echo ""
echo "==> 等待服务就绪…"
ready=0
for i in $(seq 1 60); do
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
  echo "    cd /opt/ruanzhu-platform-main && docker compose logs --tail=100"
fi
