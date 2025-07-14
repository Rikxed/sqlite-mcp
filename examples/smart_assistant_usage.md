# 智能订餐助手使用示例

## 系统概述

智能订餐助手是一个基于MCP协议的餐厅预订系统，支持餐厅查询、时段管理、预订处理和用户信息收集等功能。

## 快速开始

### 1. 启动系统

```bash
# 使用Docker启动
docker-compose up -d

# 或者直接运行Python脚本
python main_enhanced.py
```

### 2. 连接MCP客户端

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # 连接到MCP服务器
    async with stdio_client(StdioServerParameters(
        command="python", 
        args=["main_enhanced.py"]
    )) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            
            # 检查数据库状态
            result = await session.call_tool("check_database_status", {})
            print("数据库状态:", result.content[0].text)
            
            # 初始化时段库存
            result = await session.call_tool("initialize_time_slots", {})
            print("时段初始化:", result.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
```

## 数据初始化问题解决方案

### 问题1: 数据库表不存在

**症状**: 执行查询时出现"no such table"错误

**解决方案**:
```python
# 1. 检查数据库状态
result = await session.call_tool("check_database_status", {})
print(result.content[0].text)

# 2. 如果表不存在，修复数据库
result = await session.call_tool("repair_database", {})
print(result.content[0].text)
```

### 问题2: 时段库存数据缺失

**症状**: 查询可用时段时返回空结果

**解决方案**:
```python
# 初始化时段库存数据
result = await session.call_tool("initialize_time_slots", {})
print(result.content[0].text)
```

### 问题3: 基础数据缺失

**症状**: 餐厅或桌型数据为空

**解决方案**:
```python
# 1. 检查基础数据
result = await session.call_tool("sql_query", {
    "query": "SELECT COUNT(*) as count FROM restaurants"
})
print("餐厅数量:", result.content[0].text)

# 2. 如果数据缺失，修复数据库
result = await session.call_tool("repair_database", {})
print(result.content[0].text)
```

## 完整使用示例

### 示例1: 基础查询操作

```python
async def basic_queries(session):
    """基础查询操作示例"""
    
    # 1. 查询所有餐厅
    result = await session.call_tool("sql_query", {
        "query": "SELECT * FROM restaurants ORDER BY name"
    })
    print("餐厅列表:", result.content[0].text)
    
    # 2. 查询桌型信息
    result = await session.call_tool("sql_query", {
        "query": """
        SELECT 
            r.name as restaurant_name,
            tt.capacity,
            tt.quantity,
            tt.description
        FROM table_types tt 
        JOIN restaurants r ON tt.restaurant_id = r.id 
        ORDER BY r.name, tt.capacity
        """
    })
    print("桌型信息:", result.content[0].text)
    
    # 3. 查询可用时段
    result = await session.call_tool("sql_query", {
        "query": """
        SELECT 
            ts.slot_start,
            ts.slot_end,
            r.name as restaurant_name,
            tt.capacity,
            ts.available
        FROM time_slots ts 
        JOIN restaurants r ON ts.restaurant_id = r.id 
        JOIN table_types tt ON ts.table_type_id = tt.id 
        WHERE ts.available > 0 
        AND ts.slot_start >= datetime('now') 
        ORDER BY ts.slot_start, r.name
        """
    })
    print("可用时段:", result.content[0].text)
```

### 示例2: 预订流程

```python
async def booking_process(session):
    """完整预订流程示例"""
    
    # 1. 检查数据库状态
    result = await session.call_tool("check_database_status", {})
    print("数据库状态:", result.content[0].text)
    
    # 2. 确保时段库存已初始化
    result = await session.call_tool("initialize_time_slots", {})
    print("时段初始化:", result.content[0].text)
    
    # 3. 创建预订记录
    booking_operations = [
        {
            "query": """
            INSERT INTO reservations 
            (restaurant_id, table_type_id, customer_name, email, phone, people_count, slot_start, slot_end) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            "params": ["1", "3", "张三", "zhangsan@example.com", "13800138000", "4", "2024-01-15 12:00:00", "2024-01-15 14:00:00"]
        },
        {
            "query": """
            UPDATE time_slots 
            SET available = available - 1 
            WHERE restaurant_id = ? AND table_type_id = ? AND slot_start = ? AND available > 0
            """,
            "params": ["1", "3", "2024-01-15 12:00:00"]
        }
    ]
    
    result = await session.call_tool("sql_transaction", {
        "operations": booking_operations
    })
    print("预订结果:", result.content[0].text)
```

### 示例3: 用户信息管理

```python
async def user_management(session):
    """用户信息管理示例"""
    
    # 1. 查询用户预订历史
    result = await session.call_tool("sql_query", {
        "query": """
        SELECT 
            r.*, 
            res.name as restaurant_name, 
            tt.capacity, 
            tt.description
        FROM reservations r
        JOIN restaurants res ON r.restaurant_id = res.id
        JOIN table_types tt ON r.table_type_id = tt.id
        WHERE r.email = ?
        ORDER BY r.created_at DESC
        """,
        "params": ["zhangsan@example.com"]
    })
    print("用户预订历史:", result.content[0].text)
    
    # 2. 验证邮箱格式
    def validate_email(email):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    email = "zhangsan@example.com"
    if validate_email(email):
        print(f"✅ 邮箱 {email} 格式正确")
    else:
        print(f"❌ 邮箱 {email} 格式错误")
```

## 错误处理最佳实践

### 1. 数据初始化检查

```python
async def ensure_data_ready(session):
    """确保数据已准备就绪"""
    
    # 检查数据库状态
    status_result = await session.call_tool("check_database_status", {})
    status_text = status_result.content[0].text
    
    if "error" in status_text.lower():
        print("❌ 数据库状态异常，尝试修复...")
        repair_result = await session.call_tool("repair_database", {})
        print(repair_result.content[0].text)
    
    # 检查时段库存
    time_slots_result = await session.call_tool("sql_query", {
        "query": "SELECT COUNT(*) as count FROM time_slots WHERE slot_start >= datetime('now')"
    })
    
    time_slots_count = int(time_slots_result.content[0].text.split('"count": ')[1].split(',')[0])
    
    if time_slots_count == 0:
        print("⚠️ 时段库存为空，正在初始化...")
        init_result = await session.call_tool("initialize_time_slots", {})
        print(init_result.content[0].text)
    
    print("✅ 数据准备完成")
```

### 2. 事务安全操作

```python
async def safe_booking(session, booking_data):
    """安全的预订操作"""
    
    try:
        # 使用事务确保数据一致性
        operations = [
            {
                "query": """
                INSERT INTO reservations 
                (restaurant_id, table_type_id, customer_name, email, phone, people_count, slot_start, slot_end) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                "params": [
                    booking_data["restaurant_id"],
                    booking_data["table_type_id"],
                    booking_data["customer_name"],
                    booking_data["email"],
                    booking_data["phone"],
                    booking_data["people_count"],
                    booking_data["slot_start"],
                    booking_data["slot_end"]
                ]
            },
            {
                "query": """
                UPDATE time_slots 
                SET available = available - 1 
                WHERE restaurant_id = ? AND table_type_id = ? AND slot_start = ? AND available > 0
                """,
                "params": [
                    booking_data["restaurant_id"],
                    booking_data["table_type_id"],
                    booking_data["slot_start"]
                ]
            }
        ]
        
        result = await session.call_tool("sql_transaction", {
            "operations": operations
        })
        
        if "成功" in result.content[0].text:
            print("✅ 预订成功")
            return True
        else:
            print("❌ 预订失败")
            return False
            
    except Exception as e:
        print(f"❌ 预订操作异常: {e}")
        return False
```

## 环境配置

### Docker环境变量

```bash
# 数据库配置
DATABASE_PATH=/app/data/restaurants.db

# 初始化脚本
INIT_SCRIPT=/app/init/init_restaurant_system.sql

# 日志级别
LOG_LEVEL=INFO

# MCP服务器配置
MCP_SERVER_NAME=sqlite-mcp-server
MCP_SERVER_VERSION=1.0.0
```

### 本地开发环境

```bash
# 创建.env文件
cp config/example.env .env

# 修改配置
DATABASE_PATH=data/restaurants.db
INIT_SCRIPT=init/init_restaurant_system.sql
LOG_LEVEL=DEBUG
```

## 故障排除

### 常见问题

1. **连接超时**
   - 检查Docker容器是否正常运行
   - 确认端口映射正确
   - 查看容器日志

2. **数据初始化失败**
   - 检查数据库文件权限
   - 确认初始化脚本路径正确
   - 使用`repair_database`工具修复

3. **时段库存为空**
   - 使用`initialize_time_slots`工具初始化
   - 检查餐厅和桌型数据是否存在

4. **邮箱验证失败**
   - 检查邮箱格式验证逻辑
   - 确认邮箱字段不为空

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查所有可用工具
result = await session.list_tools()
print("可用工具:", result.tools)

# 检查数据库结构
result = await session.call_tool("list_tables", {})
print("数据库表:", result.content[0].text)
```

## 总结

通过以上示例和最佳实践，您可以：

1. **正确初始化系统** - 使用数据检查和修复工具
2. **安全处理预订** - 使用事务确保数据一致性
3. **有效管理用户信息** - 包含邮箱验证和格式检查
4. **快速故障排除** - 使用内置的诊断工具

记住：始终在开始操作前检查数据库状态，使用事务进行重要操作，并正确处理用户输入验证。 