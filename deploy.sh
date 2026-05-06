#!/usr/bin/env bash
# ============================================================
# 数据处理系统 - 云服务器一键部署脚本
# 支持: Ubuntu / Debian / CentOS / Rocky / AlmaLinux
# 用法: sudo bash deploy.sh
# ============================================================

set -euo pipefail

# ---------- 颜色输出 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()   { echo -e "${GREEN}[OK]${NC}    $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()  { echo -e "${RED}[ERR]${NC}   $*" >&2; }

# ---------- 基本检查 ----------
if [[ $EUID -ne 0 ]]; then
    err "请用 root 运行：sudo bash deploy.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f docker-compose.yml ]]; then
    err "未找到 docker-compose.yml，请在项目根目录执行脚本"
    exit 1
fi

# ---------- 检测系统 ----------
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    OS_ID="${ID:-}"
    OS_LIKE="${ID_LIKE:-}"
else
    err "无法识别系统，仅支持 Ubuntu/Debian/CentOS/Rocky/AlmaLinux"
    exit 1
fi

case "$OS_ID $OS_LIKE" in
    *ubuntu*|*debian*) PKG_MGR="apt" ;;
    *centos*|*rhel*|*rocky*|*almalinux*|*fedora*) PKG_MGR="dnf" ;;
    *)
        warn "未测试过的发行版：$OS_ID，尝试继续"
        if command -v apt &>/dev/null; then PKG_MGR="apt"
        elif command -v dnf &>/dev/null; then PKG_MGR="dnf"
        elif command -v yum &>/dev/null; then PKG_MGR="yum"
        else err "找不到包管理器"; exit 1
        fi
        ;;
esac
log "检测到系统：$OS_ID，使用包管理器：$PKG_MGR"

# ---------- 安装 Docker ----------
install_docker_apt() {
    log "回落：通过 apt 官方仓库直装 docker.io..."
    case "$PKG_MGR" in
        apt)
            apt-get update
            apt-get install -y docker.io
            ;;
        dnf|yum)
            $PKG_MGR install -y docker
            ;;
        *)
            return 1
            ;;
    esac
}

install_docker() {
    if command -v docker &>/dev/null; then
        ok "Docker 已安装：$(docker --version)"
        return
    fi

    log "安装 Docker..."
    local installed=0

    # 1) 官方 get-docker 脚本
    if curl -fsSL --connect-timeout 5 --max-time 15 https://get.docker.com -o /tmp/get-docker.sh 2>/dev/null; then
        log "使用 Docker 官方脚本安装..."
        if sh /tmp/get-docker.sh; then installed=1; fi
    else
        warn "官方脚本不可达（网络受限），尝试阿里云镜像..."
        # 2) 阿里云镜像
        if curl -fsSL --connect-timeout 5 --max-time 15 https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg -o /dev/null 2>/dev/null; then
            if curl -fsSL --connect-timeout 10 --max-time 30 https://get.daocloud.io/docker -o /tmp/get-docker.sh 2>/dev/null; then
                log "使用 DaoCloud 镜像脚本安装..."
                if sh /tmp/get-docker.sh --mirror Aliyun; then installed=1; fi
            fi
        fi
    fi

    # 3) 最终回落：直接装发行版仓库里的 docker
    if [[ $installed -ne 1 ]]; then
        install_docker_apt || { err "Docker 安装失败，请手动安装后重新执行"; exit 1; }
    fi

    systemctl enable --now docker
    ok "Docker 安装完成：$(docker --version)"
}

install_compose() {
    # 优先使用 docker compose plugin
    if docker compose version &>/dev/null; then
        COMPOSE_CMD="docker compose"
        ok "Docker Compose (plugin) 已就绪"
        return
    fi
    if command -v docker-compose &>/dev/null; then
        COMPOSE_CMD="docker-compose"
        ok "docker-compose (legacy) 已就绪"
        return
    fi
    log "安装 docker-compose-plugin..."
    case "$PKG_MGR" in
        apt) apt-get update && apt-get install -y docker-compose-plugin docker-compose 2>/dev/null || apt-get install -y docker-compose ;;
        dnf|yum) $PKG_MGR install -y docker-compose-plugin docker-compose 2>/dev/null || $PKG_MGR install -y docker-compose ;;
    esac
    if docker compose version &>/dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &>/dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        err "docker-compose 安装失败"
        exit 1
    fi
}

# ---------- 配置 Docker 镜像加速（国内拉镜像） ----------
configure_docker_mirror() {
    local daemon_json="/etc/docker/daemon.json"
    if [[ -f "$daemon_json" ]] && grep -q "registry-mirrors" "$daemon_json"; then
        ok "Docker 镜像加速已配置，跳过"
        return
    fi
    log "配置 Docker 镜像加速器..."
    mkdir -p /etc/docker
    cat > "$daemon_json" <<'EOF'
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me",
    "https://dockerproxy.net",
    "https://hub.rat.dev",
    "https://docker.m.daocloud.io"
  ],
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" }
}
EOF
    systemctl daemon-reload || true
    systemctl restart docker
    ok "Docker 镜像加速已配置"
}

install_docker
configure_docker_mirror
install_compose

# ---------- 国内镜像加速（pip / npm / apt / apk） ----------
# 自动检测：阿里云 ECS 默认启用；可用 USE_CN_MIRROR=0 关闭，=1 强制启用
detect_cn_mirror() {
    if [[ "${USE_CN_MIRROR:-}" == "0" ]]; then
        return 1
    fi
    if [[ "${USE_CN_MIRROR:-}" == "1" ]]; then
        return 0
    fi
    # 自动判断：阿里云 ECS metadata 可达即视为国内
    if curl -fsSL --connect-timeout 2 --max-time 3 http://100.100.100.200/latest/meta-data/ &>/dev/null; then
        return 0
    fi
    # 或系统时区是 Asia/Shanghai
    if [[ "$(cat /etc/timezone 2>/dev/null || timedatectl show -p Timezone --value 2>/dev/null)" == "Asia/Shanghai" ]]; then
        return 0
    fi
    return 1
}

if detect_cn_mirror; then
    ok "启用国内镜像加速（pip / npm / apt / apk）"
    # 阿里云 ECS 内网可直连 mirrors.cloud.aliyuncs.com（更快、不走公网流量）
    # 判断是否阿里云内网
    if curl -fsSL --connect-timeout 2 --max-time 3 http://100.100.100.200/latest/meta-data/ &>/dev/null; then
        ALI_HOST="mirrors.cloud.aliyuncs.com"
        log "检测到阿里云 ECS，使用内网镜像：$ALI_HOST"
    else
        ALI_HOST="mirrors.aliyun.com"
    fi
    export PIP_INDEX_URL="https://${ALI_HOST}/pypi/simple/"
    export PIP_TRUSTED_HOST="${ALI_HOST}"
    export APT_MIRROR="http://${ALI_HOST}"
    export NPM_REGISTRY="https://registry.npmmirror.com"
    export ALPINE_MIRROR="https://${ALI_HOST}"
else
    log "未启用国内镜像，使用默认官方源（可用 USE_CN_MIRROR=1 强制启用）"
fi

# ---------- 生成 .env ----------
ENV_FILE="$SCRIPT_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
    warn ".env 已存在，跳过生成。如需重新生成请先删除 .env"
else
    log "生成 .env（随机密钥/密码）..."
    gen_secret() { openssl rand -base64 48 | tr -d '/+=' | head -c 50; }
    gen_pwd()    { openssl rand -base64 24 | tr -d '/+=' | head -c 24; }

    DJANGO_SECRET="$(gen_secret)"
    DB_PWD="$(gen_pwd)"

    # 尝试拿公网 IP，作为 ALLOWED_HOSTS 默认值
    PUB_IP=""
    for endpoint in \
        "https://ipinfo.io/ip" \
        "https://api.ipify.org" \
        "https://ifconfig.me/ip" \
        "https://ddns.oray.com/checkip"; do
        PUB_IP="$(curl -fsSL --max-time 3 "$endpoint" 2>/dev/null || true)"
        [[ -n "$PUB_IP" ]] && break
    done
    PUB_IP="$(echo "$PUB_IP" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -n1 || true)"
    ALLOWED_HOSTS_DEFAULT="localhost,127.0.0.1"
    [[ -n "$PUB_IP" ]] && ALLOWED_HOSTS_DEFAULT="$ALLOWED_HOSTS_DEFAULT,$PUB_IP"

    cat > "$ENV_FILE" <<EOF
# 由 deploy.sh 于 $(date -u +%FT%TZ) 生成
# 生产环境请根据实际情况修改 DJANGO_ALLOWED_HOSTS / CORS_ALLOWED_ORIGINS

DJANGO_SECRET_KEY=$DJANGO_SECRET
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=$ALLOWED_HOSTS_DEFAULT

DB_NAME=data_processing
DB_USER=postgres
DB_PASSWORD=$DB_PWD

REDIS_PASSWORD=

CORS_ALLOWED_ORIGINS=http://localhost,http://127.0.0.1${PUB_IP:+,http://$PUB_IP}
EOF
    chmod 600 "$ENV_FILE"
    ok ".env 已生成"
fi

# ---------- 放开防火墙 80/8000 ----------
open_firewall() {
    if command -v ufw &>/dev/null && ufw status | grep -qi active; then
        log "配置 ufw 放行 80/443..."
        ufw allow 80/tcp  || true
        ufw allow 443/tcp || true
    elif command -v firewall-cmd &>/dev/null && systemctl is-active --quiet firewalld; then
        log "配置 firewalld 放行 80/443..."
        firewall-cmd --permanent --add-service=http  || true
        firewall-cmd --permanent --add-service=https || true
        firewall-cmd --reload || true
    else
        warn "未检测到 ufw/firewalld，跳过防火墙配置"
    fi
}
open_firewall

# ---------- 构建 & 启动 ----------
if [[ -n "${PIP_INDEX_URL:-}" ]]; then
    log "构建镜像（使用国内镜像加速：pip=$PIP_INDEX_URL）..."
else
    log "构建镜像（首次会比较慢）..."
fi
$COMPOSE_CMD build

log "启动服务（含 PostgreSQL / Redis / Django / Celery / Nginx）..."
$COMPOSE_CMD up -d

# ---------- 等数据库就绪 ----------
log "等待数据库就绪..."
for i in {1..60}; do
    if $COMPOSE_CMD exec -T db pg_isready -U "${DB_USER:-postgres}" &>/dev/null; then
        ok "数据库就绪"
        break
    fi
    sleep 2
    [[ $i -eq 60 ]] && { err "数据库启动超时，看日志：$COMPOSE_CMD logs db"; exit 1; }
done

# ---------- 等后端就绪 ----------
log "等待后端容器启动..."
for i in {1..30}; do
    if $COMPOSE_CMD exec -T backend python -c "import django" &>/dev/null; then
        break
    fi
    sleep 2
done

# ---------- 数据库初始化 ----------
log "执行数据库迁移..."
$COMPOSE_CMD exec -T backend python manage.py migrate --noinput

log "收集静态文件..."
$COMPOSE_CMD exec -T backend python manage.py collectstatic --noinput || true

# ---------- 创建/更新管理员账号 ----------
ADMIN_USERNAME="${DJANGO_SUPERUSER_USERNAME:-admin}"
ADMIN_PASSWORD="${DJANGO_SUPERUSER_PASSWORD:-admin@123}"
ADMIN_EMAIL="${DJANGO_SUPERUSER_EMAIL:-admin@example.com}"

log "创建/更新管理员账号：$ADMIN_USERNAME"
$COMPOSE_CMD exec -T \
    -e ADMIN_USERNAME="$ADMIN_USERNAME" \
    -e ADMIN_PASSWORD="$ADMIN_PASSWORD" \
    -e ADMIN_EMAIL="$ADMIN_EMAIL" \
    backend python manage.py shell <<'PYEOF'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ['ADMIN_USERNAME']
password = os.environ['ADMIN_PASSWORD']
email = os.environ['ADMIN_EMAIL']

user, created = User.objects.get_or_create(
    username=username,
    defaults={'email': email, 'is_staff': True, 'is_superuser': True, 'role': 'super_admin'},
)
user.email = email
user.is_staff = True
user.is_superuser = True
user.is_active = True
if hasattr(user, 'role'):
    user.role = 'super_admin'
user.set_password(password)
user.save()
print(f"[OK] {'Created' if created else 'Updated'} superuser: {username}")
PYEOF
ok "管理员账号就绪"

# ---------- 完成 ----------
echo
ok "部署完成！"
echo
echo "服务状态："
$COMPOSE_CMD ps
echo
PUB_IP=""
for endpoint in "https://ipinfo.io/ip" "https://api.ipify.org" "https://ifconfig.me/ip"; do
    PUB_IP="$(curl -fsSL --max-time 3 "$endpoint" 2>/dev/null || true)"
    [[ -n "$PUB_IP" ]] && break
done
PUB_IP="$(echo "$PUB_IP" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -n1 || echo '<服务器IP>')"
cat <<EOF
──────────────────────────────────────────────
访问地址：
  前端（Nginx）：http://$PUB_IP
  后端 API：    http://$PUB_IP:8000/api/
  Admin 后台：  http://$PUB_IP/admin/   （走前端 Nginx 反代）

管理员账号：
  用户名：$ADMIN_USERNAME
  密  码：$ADMIN_PASSWORD

$(echo -e "${RED}⚠ 默认密码是弱密码，首次登录后请立刻在"个人中心"修改！${NC}")

服务架构（全部由 docker compose 管理）：
  - db        PostgreSQL 16
  - redis     Redis 7
  - backend   Django + Gunicorn
  - celery    Celery Worker
  - frontend  Nginx + Vue 静态文件  (端口 80)

常用命令：
  查看日志：$COMPOSE_CMD logs -f backend
  重启：   $COMPOSE_CMD restart
  停止：   $COMPOSE_CMD down
  进入后端：$COMPOSE_CMD exec backend bash

下一步：
  1. 编辑 .env 把 DJANGO_ALLOWED_HOSTS / CORS_ALLOWED_ORIGINS 改成你的域名
  2. 如需 HTTPS，建议前面挂云厂商 SLB/CDN 或 Caddy 处理 SSL
──────────────────────────────────────────────
EOF
