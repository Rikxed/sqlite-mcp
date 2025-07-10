#!/bin/bash

echo "🚀 启动网络版MCP服务器..."
echo "📁 初始化数据库..."

# 如果数据库文件不存在则初始化表结构和数据
if [ ! -f "$DATABASE_PATH" ]; then
    echo "⚡ 正在初始化餐厅数据库表结构和数据..."
    sqlite3 "$DATABASE_PATH" < /app/init/init_restaurant_system.sql
    if [ $? -ne 0 ]; then
        echo "❌ 餐厅数据库初始化失败"
        exit 1
    fi
    echo "✅ 餐厅数据库初始化完成"
else
    echo "数据库文件已存在，跳过初始化"
fi

echo "🌐 启动网络版MCP服务器..."
echo "✅ 服务启动完成，开始监听..."

# 启动网络版MCP服务器
python main_network.py 