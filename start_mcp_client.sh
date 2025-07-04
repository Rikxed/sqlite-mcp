#!/bin/bash

echo "🚀 启动MCP客户端连接模式..."

# 检查数据库是否存在，如果不存在则初始化
if [ ! -f "$DATABASE_PATH" ]; then
    echo "📁 初始化数据库..."
    sqlite3 "$DATABASE_PATH" < /app/init/init_restaurant_system.sql
    if [ $? -ne 0 ]; then
        echo "❌ 数据库初始化失败"
        exit 1
    fi
    echo "✅ 数据库初始化完成"
    
    echo "⏰ 初始化时段库存..."
    python scripts/init_time_slots.py
    if [ $? -eq 0 ]; then
        echo "✅ 时段库存初始化完成"
    else
        echo "⚠️  时段库存初始化失败，但继续启动服务器"
    fi
fi

echo "🌐 启动MCP服务器 (stdio模式)..."
echo "✅ 服务启动完成，开始监听..."

# 直接启动MCP服务器，不等待用户输入
exec python main_enhanced.py 