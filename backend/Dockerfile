FROM python:3.12-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 构建参数（国内镜像加速，默认走官方源，由 deploy.sh 注入阿里云镜像）
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_TRUSTED_HOST=pypi.org
ARG APT_MIRROR=""

WORKDIR /app

# 可选：替换 Debian apt 源为国内镜像（在安装系统依赖前）
RUN if [ -n "$APT_MIRROR" ]; then \
        sed -i "s|http://deb.debian.org|$APT_MIRROR|g; s|http://security.debian.org|$APT_MIRROR|g" \
            /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
        sed -i "s|http://deb.debian.org|$APT_MIRROR|g; s|http://security.debian.org|$APT_MIRROR|g" \
            /etc/apt/sources.list 2>/dev/null || true; \
    fi

# 安装系统依赖 (PostgreSQL client)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        build-essential \
        gosu && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（国内用阿里云 PyPI 镜像加速）
COPY requirements.txt .
RUN pip install --no-cache-dir \
        --index-url "$PIP_INDEX_URL" \
        --trusted-host "$PIP_TRUSTED_HOST" \
        --timeout 120 \
        --retries 5 \
        -r requirements.txt

# 复制项目代码
COPY . .

# 创建日志和 media 目录
# 注意：media 目录需要在 docker 命名卷首次挂载前就建好并 chown，
# 新卷挂载时会从镜像继承目录所有权；已存在的卷需手工 chown 一次
RUN mkdir -p logs media/uploads media/processing_results

# 收集静态文件
RUN python manage.py collectstatic --noinput || true

# 创建非 root 用户并设置目录权限
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

# 入口脚本: 以 root 修复 media / logs 卷权限后 gosu 切到 appuser
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 注意：不要 USER appuser, 交给 entrypoint 用 gosu 切换
ENTRYPOINT ["docker-entrypoint.sh"]

EXPOSE 8000

# 使用 gunicorn 启动（生产环境）
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
