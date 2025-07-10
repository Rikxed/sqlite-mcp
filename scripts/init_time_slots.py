#!/usr/bin/env python3
"""
初始化时段库存脚本
为餐厅预订系统生成未来7天的时段库存数据
只在Docker启动时运行一次
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_path():
    """获取数据库路径"""
    # 优先使用环境变量
    db_path = os.getenv('DATABASE_PATH', 'data/sqlite.db')
    
    # 如果是相对路径，转换为绝对路径
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.getcwd(), db_path)
    
    return db_path


def check_if_time_slots_exist(cursor):
    """检查时段库存是否已存在"""
    cursor.execute("SELECT COUNT(*) FROM time_slots")
    count = cursor.fetchone()[0]
    return count > 0


def generate_time_slots(days=7, open_time="09:00", close_time="21:00", slot_hours=2):
    """
    生成时段库存数据
    
    Args:
        days: 生成未来几天的数据
        open_time: 开门时间 (HH:MM)
        close_time: 关门时间 (HH:MM)
        slot_hours: 每个时段时长(小时)
    """
    db_path = get_db_path()
    
    # 确保数据库文件存在
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查时段库存是否已存在
        if check_if_time_slots_exist(cursor):
            logger.info("时段库存数据已存在，跳过初始化")
            conn.close()
            return True
        
        logger.info(f"开始生成未来{days}天的时段库存数据...")
        
        # 获取所有餐厅
        cursor.execute("SELECT id, name FROM restaurants")
        restaurants = cursor.fetchall()
        
        if not restaurants:
            logger.warning("没有找到餐厅数据，请先运行init.sql初始化基础数据")
            conn.close()
            return False
        
        # 获取所有桌型
        cursor.execute("SELECT id, restaurant_id, capacity, quantity FROM table_types")
        table_types = cursor.fetchall()
        
        if not table_types:
            logger.warning("没有找到桌型数据，请先运行init.sql初始化基础数据")
            conn.close()
            return False
        
        # 优化：使用批量插入和事务
        cursor.execute("BEGIN TRANSACTION")
        
        # 准备批量插入的数据
        batch_data = []
        slots_created = 0
        
        for restaurant_id, restaurant_name in restaurants:
            logger.info(f"为餐厅 '{restaurant_name}' 生成时段库存...")
            
            # 获取该餐厅的所有桌型
            restaurant_table_types = [tt for tt in table_types if tt[1] == restaurant_id]
            
            for day in range(days):
                date = (datetime.now() + timedelta(days=day)).date()
                
                # 解析时间
                start_hour = int(open_time.split(":")[0])
                end_hour = int(close_time.split(":")[0])
                
                # 生成该天的所有时段
                for hour in range(start_hour, end_hour, slot_hours):
                    slot_start = datetime.combine(date, datetime.min.time()).replace(hour=hour)
                    slot_end = slot_start + timedelta(hours=slot_hours)
                    
                    # 为每种桌型生成库存
                    for table_type_id, _, capacity, quantity in restaurant_table_types:
                        batch_data.append((
                            restaurant_id,
                            table_type_id,
                            slot_start,
                            slot_end,
                            quantity,  # available
                            quantity   # total
                        ))
                        slots_created += 1
        
        # 批量插入所有数据
        logger.info(f"批量插入 {len(batch_data)} 条时段库存记录...")
        cursor.executemany(
            """
            INSERT OR IGNORE INTO time_slots (
                restaurant_id, table_type_id, slot_start, slot_end, available, total
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            batch_data
        )
        
        cursor.execute("COMMIT")
        conn.close()
        
        logger.info(f"时段库存初始化完成！共生成 {slots_created} 条记录")
        return True
        
    except Exception as e:
        logger.error(f"生成时段库存时出错: {e}")
        try:
            cursor.execute("ROLLBACK")
        except:
            pass
        return False


def main():
    """主函数"""
    try:
        logger.info("开始初始化时段库存...")
        
        # 配置参数
        days = int(os.getenv('INIT_DAYS', '7'))  # 生成未来天数
        open_time = os.getenv('RESTAURANT_OPEN_TIME', '09:00')  # 开门时间
        close_time = os.getenv('RESTAURANT_CLOSE_TIME', '21:00')  # 关门时间
        slot_hours = int(os.getenv('SLOT_HOURS', '2'))  # 时段时长
        
        logger.info(f"配置参数: 未来{days}天, 营业时间{open_time}-{close_time}, 时段{slot_hours}小时")
        
        # 生成时段库存
        success = generate_time_slots(days, open_time, close_time, slot_hours)
        
        if success:
            logger.info("时段库存初始化成功！")
            sys.exit(0)
        else:
            logger.error("时段库存初始化失败！")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"初始化过程中出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 