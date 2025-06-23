#!/usr/bin/env python3
"""
直接查询数据库内容
展示数据初始化的结果
"""

import sqlite3
import os
from datetime import datetime


def connect_db():
    """连接数据库"""
    db_path = "data/sqlite.db"
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        return conn
    except Exception as e:
        print(f"❌ 连接数据库失败: {e}")
        return None


def show_database_info(conn):
    """显示数据库信息"""
    print("🔍 数据库信息:")
    print(f"   数据库路径: {os.path.abspath('data/sqlite.db')}")
    print(f"   数据库大小: {os.path.getsize('data/sqlite.db') / 1024:.2f} KB")
    print(f"   当前时间: {datetime.now()}")
    print()


def show_tables(conn):
    """显示所有表"""
    print("📋 数据库表:")
    cursor = conn.execute("""
        SELECT name, sql FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    
    tables = cursor.fetchall()
    for table in tables:
        print(f"   - {table['name']}")
    print()


def show_restaurants(conn):
    """显示餐厅数据"""
    print("🍽️ 餐厅数据:")
    cursor = conn.execute("SELECT * FROM restaurants ORDER BY id")
    restaurants = cursor.fetchall()
    
    if restaurants:
        print("   ID | 名称 | 地址 | 电话 | 营业时间")
        print("   ---|------|------|------|---------")
        for restaurant in restaurants:
            # 获取列名
            columns = [description[0] for description in cursor.description]
            print(f"   列名: {columns}")  # 调试信息
            print(f"   数据: {dict(restaurant)}")  # 调试信息
            break  # 只显示第一条记录用于调试
    else:
        print("   ❌ 无餐厅数据")
    print()


def show_table_types(conn):
    """显示桌型数据"""
    print("🪑 桌型数据:")
    cursor = conn.execute("""
        SELECT 
            r.name as restaurant_name,
            tt.id,
            tt.capacity,
            tt.quantity,
            tt.description
        FROM table_types tt
        JOIN restaurants r ON tt.restaurant_id = r.id
        ORDER BY r.name, tt.capacity
    """)
    table_types = cursor.fetchall()
    
    if table_types:
        print("   餐厅 | 桌型ID | 容量 | 数量 | 描述")
        print("   -----|--------|------|------|------")
        for tt in table_types:
            print(f"   {tt['restaurant_name']} | {tt['id']:6d} | {tt['capacity']:4d}人 | {tt['quantity']:4d}张 | {tt['description']}")
    else:
        print("   ❌ 无桌型数据")
    print()


def show_time_slots(conn):
    """显示时段库存数据"""
    print("⏰ 时段库存数据:")
    
    # 显示最近的时段
    cursor = conn.execute("""
        SELECT 
            r.name as restaurant_name,
            tt.capacity,
            ts.slot_start,
            ts.slot_end,
            ts.available,
            ts.total
        FROM time_slots ts
        JOIN restaurants r ON ts.restaurant_id = r.id
        JOIN table_types tt ON ts.table_type_id = tt.id
        WHERE ts.slot_start >= datetime('now')
        ORDER BY ts.slot_start
        LIMIT 15
    """)
    time_slots = cursor.fetchall()
    
    if time_slots:
        print("   餐厅 | 容量 | 开始时间 | 结束时间 | 可用/总数")
        print("   -----|------|----------|----------|----------")
        for ts in time_slots:
            start_time = datetime.fromisoformat(ts['slot_start']).strftime('%m-%d %H:%M')
            end_time = datetime.fromisoformat(ts['slot_end']).strftime('%H:%M')
            print(f"   {ts['restaurant_name']} | {ts['capacity']:4d}人 | {start_time} | {end_time} | {ts['available']:2d}/{ts['total']:2d}")
    else:
        print("   ❌ 无时段库存数据")
    print()


def show_time_slots_summary(conn):
    """显示时段库存统计"""
    print("📊 时段库存统计:")
    
    # 统计每个餐厅的时段数量
    cursor = conn.execute("""
        SELECT 
            r.name as restaurant_name,
            COUNT(*) as total_slots,
            SUM(CASE WHEN ts.slot_start >= datetime('now') THEN 1 ELSE 0 END) as future_slots,
            SUM(ts.available) as total_available,
            SUM(ts.total) as total_capacity
        FROM time_slots ts
        JOIN restaurants r ON ts.restaurant_id = r.id
        GROUP BY r.id, r.name
        ORDER BY r.name
    """)
    summary = cursor.fetchall()
    
    if summary:
        print("   餐厅 | 总时段数 | 未来时段 | 总可用/总容量")
        print("   -----|----------|----------|-------------")
        for row in summary:
            print(f"   {row['restaurant_name']} | {row['total_slots']:8d} | {row['future_slots']:8d} | {row['total_available']:3d}/{row['total_capacity']:3d}")
    else:
        print("   ❌ 无统计数据")
    print()


def show_sample_queries():
    """显示示例查询"""
    print("💡 MCP工具使用示例:")
    print()
    print("1. 查询可用时段:")
    print('   {"name": "sql_query", "arguments": {"query": "SELECT r.name, tt.capacity, ts.slot_start, ts.slot_end, ts.available FROM time_slots ts JOIN restaurants r ON ts.restaurant_id = r.id JOIN table_types tt ON ts.table_type_id = tt.id WHERE ts.available > 0 AND ts.slot_start >= datetime(\'now\') ORDER BY ts.slot_start LIMIT 10"}}')
    print()
    print("2. 预订餐桌 (减少可用数量):")
    print('   {"name": "sql_update", "arguments": {"query": "UPDATE time_slots SET available = available - 1 WHERE restaurant_id = 1 AND table_type_id = 1 AND slot_start = \'2024-01-15 18:00:00\' AND available > 0"}}')
    print()
    print("3. 查询餐厅信息:")
    print('   {"name": "sql_query", "arguments": {"query": "SELECT * FROM restaurants"}}')
    print()
    print("4. 查询桌型信息:")
    print('   {"name": "sql_query", "arguments": {"query": "SELECT r.name, tt.capacity, tt.quantity FROM table_types tt JOIN restaurants r ON tt.restaurant_id = r.id"}}')
    print()


def main():
    """主函数"""
    print("🧪 数据库内容查询")
    print("=" * 50)
    
    # 连接数据库
    conn = connect_db()
    if not conn:
        return
    
    try:
        # 显示数据库信息
        show_database_info(conn)
        
        # 显示表结构
        show_tables(conn)
        
        # 显示餐厅数据
        show_restaurants(conn)
        
        # 显示桌型数据
        show_table_types(conn)
        
        # 显示时段库存数据
        show_time_slots(conn)
        
        # 显示统计信息
        show_time_slots_summary(conn)
        
        # 显示使用示例
        show_sample_queries()
        
    finally:
        conn.close()
    
    print("✅ 查询完成！")


if __name__ == "__main__":
    main() 