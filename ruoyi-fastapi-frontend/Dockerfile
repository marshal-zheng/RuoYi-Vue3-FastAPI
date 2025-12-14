# 构建阶段
FROM docker.1ms.run/library/node:20-alpine AS builder

WORKDIR /app

# 复制 package.json 和 yarn 配置文件
COPY package.json yarn.lock .npmrc .yarnrc.yml ./

# 配置 Alpine 国内镜像源（加速系统依赖安装）
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# 配置 npm 镜像
RUN npm config set registry https://registry.npmmirror.com

# 启用 corepack 并安装 packageManager 指定的 yarn 版本
RUN corepack enable && corepack prepare yarn@4.9.2 --activate

# 配置 yarn 镜像
RUN yarn config set npmRegistryServer https://registry.npmmirror.com

# 安装依赖
RUN yarn install --frozen-lockfile

# 复制项目文件
COPY . .

# 构建生产版本
RUN yarn build:prod

# 生产阶段
FROM docker.1ms.run/library/nginx:alpine

# 配置 Alpine 国内镜像源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# 可选：安装必要的工具（如需要）
# RUN apk add --no-cache tzdata && ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone

# 复制构建产物到 nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]