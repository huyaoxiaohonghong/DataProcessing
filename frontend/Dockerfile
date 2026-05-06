FROM node:20-alpine AS build

WORKDIR /app

# 构建参数（国内镜像加速，默认走官方源）
ARG NPM_REGISTRY=https://registry.npmjs.org
ARG ALPINE_MIRROR=""

# 可选：替换 Alpine apk 源为国内镜像
RUN if [ -n "$ALPINE_MIRROR" ]; then \
        sed -i "s|https\\?://dl-cdn.alpinelinux.org|$ALPINE_MIRROR|g" /etc/apk/repositories; \
    fi

# 配置 npm 源并安装依赖
COPY package.json package-lock.json ./
RUN npm config set registry "$NPM_REGISTRY" && \
    npm config set fetch-retries 5 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm ci --no-audit --no-fund

# 构建
COPY . .
RUN npm run build

# 部署阶段
FROM nginx:alpine

ARG ALPINE_MIRROR=""
RUN if [ -n "$ALPINE_MIRROR" ]; then \
        sed -i "s|https\\?://dl-cdn.alpinelinux.org|$ALPINE_MIRROR|g" /etc/apk/repositories; \
    fi

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
