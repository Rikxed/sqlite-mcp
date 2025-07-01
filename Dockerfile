FROM python:3.11-slim

WORKDIR /app

# 使用国内镜像源加速下载 - 修复apt源配置
RUN echo "deb https://mirrors.aliyun.com/debian/ bullseye main non-free contrib" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian/ bullseye-updates main non-free contrib" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian/ bullseye-backports main non-free contrib" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security bullseye-security main non-free contrib" >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    sqlite3 \
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

# 设置健康检查脚本权限
RUN chmod +x /app/health_check.py

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "🚀 启动MCP服务器..."\n\
echo "📁 初始化数据库..."\n\
python -c "from database.connection import db_manager; print(\"✅ 数据库初始化完成\")"\n\
if [ $? -ne 0 ]; then\n\
    echo "❌ 数据库初始化失败"\n\
    exit 1\n\
fi\n\
echo "⏰ 初始化时段库存..."\n\
python scripts/init_time_slots.py\n\
if [ $? -eq 0 ]; then\n\
    echo "✅ 时段库存初始化完成"\n\
else\n\
    echo "⚠️  时段库存初始化失败，但继续启动服务器"\n\
fi\n\
echo "🌐 启动MCP服务器 (stdio模式)..."\n\
echo "🔍 等待服务启动完成..."\n\
sleep 2\n\
echo "✅ 服务启动完成，开始监听..."\n\
# 直接运行MCP服务器，不使用exec\n\
python main_enhanced.py' > /app/start.sh && chmod +x /app/start.sh

# 设置入口点
ENTRYPOINT ["/app/start.sh"] 