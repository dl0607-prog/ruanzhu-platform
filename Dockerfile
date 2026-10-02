# 软著工场 · 后端服务镜像
# 构建：docker build -t ruanzhu-platform .
# 运行：docker run -p 8310:8310 -v $(pwd)/data:/app/data -v $(pwd)/exports:/app/exports ruanzhu-platform
FROM python:3.11-slim

WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend
COPY start.sh /app/start.sh

# LLM 配置通过环境变量或挂载 .env 注入：
#   docker run -e LLM_API_KEY=sk-xxx -e LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4 ...
ENV LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4

EXPOSE 8310
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8310"]
