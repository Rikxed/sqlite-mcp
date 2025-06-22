#!/usr/bin/env python3
"""
测试时段库存数据脚本
验证时段库存是否正确生成
"""

import sqlite3
import os
from datetime import datetime


def test_time_slots():
    """测试时段库存数据"""
    db_path = os.getenv('DATABASE_PATH', 'data/sqlite.db')
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查餐厅数据
        cursor.execute("SELECT id, name FROM restaurants")
        restaurants = cursor.fetchall()
        print(f"📋 餐厅数量: {len(restaurants)}")
        for rid, name in restaurants:
            print(f"   - {name} (ID: {rid})")
        
        # 检查桌型数据
        cursor.execute("SELECT id, restaurant_id, capacity, quantity FROM table_types")
        table_types = cursor.fetchall()
        print(f"🪑 桌型数量: {len(table_types)}")
        for ttid, rid, capacity, quantity in table_types:
            restaurant_name = next((name for rid2, name in restaurants if rid2 == rid), "未知")
            print(f"   - {restaurant_name}: {capacity}人桌 x {quantity}张 (ID: {ttid})")
        
        # 检查时段库存数据
        cursor.execute("SELECT COUNT(*) FROM time_slots")
        time_slots_count = cursor.fetchone()[0]
        print(f"⏰ 时段库存记录数: {time_slots_count}")
        
        if time_slots_count > 0:
            # 显示一些示例数据
            cursor.execute("""
                SELECT 
                    r.name as restaurant_name,
                    tt.capacity,
                    ts.slot_start,
                    ts.slot_end,
                    ts.available
                FROM time_slots ts
                JOIN restaurants r ON ts.restaurant_id = r.id
                JOIN table_types tt ON ts.table_type_id = tt.id
                ORDER BY ts.slot_start
                LIMIT 10
            """)
            
            print("\n📊 时段库存示例:")
            for restaurant_name, capacity, slot_start, slot_end, available in cursor.fetchall():
                print(f"   - {restaurant_name} {capacity}人桌: {slot_start} - {slot_end} (可用: {available})")
            
            # 统计每个餐厅的时段数量
            cursor.execute("""
                SELECT 
                    r.name,
                    COUNT(*) as slot_count
                FROM time_slots ts
                JOIN restaurants r ON ts.restaurant_id = r.id
                GROUP BY r.id, r.name
            """)
            
            print("\n📈 各餐厅时段统计:")
            for restaurant_name, slot_count in cursor.fetchall():
                print(f"   - {restaurant_name}: {slot_count} 个时段")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🧪 开始测试时段库存数据...")
    success = test_time_slots()
    if success:
        print("✅ 测试完成")
    else:
        print("❌ 测试失败") 