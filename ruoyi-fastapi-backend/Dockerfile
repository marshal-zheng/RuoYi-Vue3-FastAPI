FROM docker.1ms.run/python:3.11-slim

WORKDIR /app

RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|security.debian.org|mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p vf_admin/upload_path vf_admin/download_path vf_admin/gen_path logs

# 确保脚本有执行权限
RUN chmod +x docker-entrypoint.sh scripts/db_migrate.sh

# 设置环境变量
ENV APP_ENV=prod
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 使用 entrypoint 进行数据库初始化
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# 默认启动命令
CMD ["python", "app.py"]
