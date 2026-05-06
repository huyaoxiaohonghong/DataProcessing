FROM python:3.12-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 安装系统依赖 (PostgreSQL client)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 收集静态文件
RUN python manage.py collectstatic --noinput || true

# 创建非 root 用户并设置目录权限
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# 使用 gunicorn 启动（生产环境）
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
