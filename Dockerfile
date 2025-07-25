FROM python:3.11-slim

WORKDIR /app

# 使用国内镜像源加速下载 - 修复apt源配置
RUN echo "deb https://mirrors.aliyun.com/debian/ bullseye main non-free contrib" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian/ bullseye-updates main non-free contrib" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security bullseye-security main non-free contrib" >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 使用国内PyPI镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data /app/config /app/init /app/scripts

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/data/restaurants.db
ENV INIT_SCRIPT=/app/init/init.sql

# 设置脚本权限
RUN chmod +x /app/health_check.py /app/start.sh /app/start_mcp_client.sh

# 设置入口点
ENTRYPOINT ["/app/start.sh"] 
