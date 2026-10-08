FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt && useradd --uid 10001 --create-home appuser
COPY backend /app/backend
COPY frontend /app/frontend
RUN mkdir -p /app/data /app/exports && chown -R appuser:appuser /app/data /app/exports
USER appuser
WORKDIR /app/backend
EXPOSE 8310
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8310", "--no-proxy-headers"]
