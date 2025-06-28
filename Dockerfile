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
RUN mkdir -p /app/data /app/config /app/init /app/scripts

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/data/restaurants.db
ENV INIT_SCRIPT=/app/init/init.sql

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "🚀 启动MCP服务器..."\n\
echo "📁 初始化数据库..."\n\
python -c "from database.connection import db_manager; print(\"✅ 数据库初始化完成\")"\n\
echo "⏰ 初始化时段库存..."\n\
python scripts/init_time_slots.py\n\
if [ $? -eq 0 ]; then\n\
    echo "✅ 时段库存初始化完成"\n\
else\n\
    echo "⚠️  时段库存初始化失败，但继续启动服务器"\n\
fi\n\
echo "🌐 启动MCP服务器 (stdio模式)..."\n\
exec "$@"' > /app/start.sh && chmod +x /app/start.sh

# 设置入口点
ENTRYPOINT ["/app/start.sh"] 