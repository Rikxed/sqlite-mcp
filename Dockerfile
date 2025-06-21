FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data /app/config /app/init

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/data/sqlite.db
ENV INIT_SCRIPT=/app/init/init.sql

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "🚀 启动SQLite MCP服务器..."\n\
echo "📁 初始化数据库..."\n\
python -c "from database.connection import db_manager; print(\"✅ 数据库初始化完成\")"\n\
echo "🌐 启动MCP服务器 (stdio模式)..."\n\
exec python main.py' > /app/start.sh && chmod +x /app/start.sh

# 设置入口点
ENTRYPOINT ["/app/start.sh"] 