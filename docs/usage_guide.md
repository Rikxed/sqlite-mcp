# SQLite MCP服务器使用指南

## 概述

SQLite MCP服务器提供了两种运行模式：
1. **标准模式**：与原来完全兼容，适用于单Agent场景
2. **增强模式**：支持多Agent并发控制，适用于多Agent场景

## 启动方式

### 1. 标准模式（与原来相同）

#### 直接运行
```bash
python main.py
```

#### Docker运行
```bash
docker run --rm -i \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/init:/app/init \
  -e DATABASE_PATH=/app/data/sqlite.db \
  -e INIT_SCRIPT=/app/init/init.sql \
  db-sqlite-mcp-server
```

#### 使用脚本
```bash
./query.sh users
./query.sh query "SELECT * FROM products WHERE price > 100"
```

### 2. 增强模式（多Agent并发控制）

#### 直接运行
```bash
# 启动Agent 1
AGENT_ID=agent-1 USE_THREAD_SAFE=true python main_enhanced.py

# 启动Agent 2
AGENT_ID=agent-2 USE_THREAD_SAFE=true python main_enhanced.py
```

#### Docker运行
```bash
# 启动Agent 1
docker run --rm -i \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/init:/app/init \
  -e DATABASE_PATH=/app/data/sqlite.db \
  -e INIT_SCRIPT=/app/init/init.sql \
  -e AGENT_ID=agent-1 \
  -e USE_THREAD_SAFE=true \
  db-sqlite-mcp-server python main_enhanced.py

# 启动Agent 2
docker run --rm -i \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/init:/app/init \
  -e DATABASE_PATH=/app/data/sqlite.db \
  -e INIT_SCRIPT=/app/init/init.sql \
  -e AGENT_ID=agent-2 \
  -e USE_THREAD_SAFE=true \
  db-sqlite-mcp-server python main_enhanced.py
```

## 可用工具列表

### 标准模式工具

#### 1. sql_query
执行SQL查询语句，返回查询结果。

**参数:**
- `query` (string, 必需): SQL查询语句
- `params` (array, 可选): 查询参数列表

**示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "sql_query",
    "arguments": {
      "query": "SELECT * FROM users WHERE age > ?",
      "params": ["18"]
    }
  }
}
```

#### 2. sql_update
执行SQL更新语句（INSERT、UPDATE、DELETE）。

**参数:**
- `query` (string, 必需): SQL更新语句
- `params` (array, 可选): 更新参数列表

**示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "sql_update",
    "arguments": {
      "query": "INSERT INTO users (name, age) VALUES (?, ?)",
      "params": ["张三", "25"]
    }
  }
}
```

#### 3. list_tables
列出数据库中的所有表。

**参数:** 无

**示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list_tables",
    "arguments": {}
  }
}
```

#### 4. describe_table
描述指定表的结构。

**参数:**
- `table_name` (string, 必需): 表名

**示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "describe_table",
    "arguments": {
      "table_name": "users"
    }
  }
}
```

#### 5. create_table
创建新表。

**参数:**
- `table_name` (string, 必需): 表名
- `columns` (string, 必需): 列定义SQL语句

**示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "create_table",
    "arguments": {
      "table_name": "users",
      "columns": "id INTEGER PRIMARY KEY, name TEXT NOT NULL, age INTEGER"
    }
  }
}
```

#### 6. database_info
获取数据库基本信息。

**参数:** 无

**示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "database_info",
    "arguments": {}
  }
}
```

### 增强模式工具（新增）

#### 1. sql_query（增强版）
支持一致性级别控制。

**参数:**
- `query` (string, 必需): SQL查询语句
- `params` (array, 可选): 查询参数列表
- `consistency_level` (string, 可选): 一致性级别 ("read_uncommitted", "read_committed", "serializable")

**示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "sql_query",
    "arguments": {
      "query": "SELECT * FROM users WHERE age > ?",
      "params": ["18"],
      "consistency_level": "serializable"
    }
  }
}
```

#### 2. sql_update（增强版）
支持乐观锁控制。

**参数:**
- `query` (string, 必需): SQL更新语句
- `params` (array, 可选): 更新参数列表
- `use_optimistic_lock` (boolean, 可选): 是否使用乐观锁
- `version_column` (string, 可选): 版本列名
- `version_value` (integer, 可选): 期望的版本值

**示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "sql_update",
    "arguments": {
      "query": "UPDATE users SET name = ?, version = ? WHERE id = ? AND version = ?",
      "params": ["新名字", "2", "1", "1"],
      "use_optimistic_lock": true,
      "version_column": "version",
      "version_value": 1
    }
  }
}
```

#### 3. sql_transaction（新增）
执行事务操作，支持多个SQL语句的原子性执行。

**参数:**
- `operations` (array, 必需): 操作列表
- `isolation_level` (string, 可选): 隔离级别 ("read_uncommitted", "read_committed", "serializable")

**示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "sql_transaction",
    "arguments": {
      "operations": [
        {
          "query": "INSERT INTO users (name, age) VALUES (?, ?)",
          "params": ["用户1", "25"]
        },
        {
          "query": "INSERT INTO products (name, price) VALUES (?, ?)",
          "params": ["产品1", "100.0"]
        }
      ],
      "isolation_level": "serializable"
    }
  }
}
```

#### 4. agent_status（新增）
获取当前Agent的状态信息。

**参数:** 无

**示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "agent_status",
    "arguments": {}
  }
}
```

#### 5. transaction_history（新增）
获取事务历史记录。

**参数:**
- `limit` (integer, 可选): 返回的记录数量限制

**示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "transaction_history",
    "arguments": {
      "limit": 50
    }
  }
}
```

## 使用场景

### 1. 单Agent场景（标准模式）
- 单个MCP Agent访问数据库
- 简单的数据查询和更新
- 不需要并发控制

**启动命令:**
```bash
python main.py
```

### 2. 多Agent场景（增强模式）
- 多个MCP Agent同时访问数据库
- 需要避免脏读和脏写
- 需要事务一致性保证

**启动命令:**
```bash
# Agent 1
AGENT_ID=agent-1 USE_THREAD_SAFE=true python main_enhanced.py

# Agent 2
AGENT_ID=agent-2 USE_THREAD_SAFE=true python main_enhanced.py
```

### 3. 高并发场景
- 大量并发读写操作
- 需要乐观锁控制
- 需要事务隔离

**使用示例:**
```json
// 高一致性查询
{
  "name": "sql_query",
  "arguments": {
    "query": "SELECT * FROM users WHERE id = ?",
    "params": ["1"],
    "consistency_level": "serializable"
  }
}

// 乐观锁更新
{
  "name": "sql_update",
  "arguments": {
    "query": "UPDATE users SET balance = balance + ?, version = ? WHERE id = ? AND version = ?",
    "params": ["100", "2", "1", "1"],
    "use_optimistic_lock": true,
    "version_column": "version",
    "version_value": 1
  }
}

// 事务操作
{
  "name": "sql_transaction",
  "arguments": {
    "operations": [
      {
        "query": "UPDATE accounts SET balance = balance - ? WHERE id = ?",
        "params": ["100", "1"]
      },
      {
        "query": "UPDATE accounts SET balance = balance + ? WHERE id = ?",
        "params": ["100", "2"]
      }
    ],
    "isolation_level": "serializable"
  }
}
```

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DATABASE_PATH` | `data/sqlite.db` | 数据库文件路径 |
| `INIT_SCRIPT` | `None` | 初始化脚本路径 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `AGENT_ID` | `自动生成` | Agent唯一标识符 |
| `USE_THREAD_SAFE` | `false` | 是否使用线程安全模式 |

### 配置文件

创建 `.env` 文件：
```env
# 数据库配置
DATABASE_PATH=data/sqlite.db

# 初始化配置
INIT_SCRIPT=init/init.sql

# 日志配置
LOG_LEVEL=INFO

# Agent配置
AGENT_ID=my-agent-1
USE_THREAD_SAFE=true
```

## 最佳实践

### 1. 选择合适的模式
- **单Agent**：使用标准模式
- **多Agent**：使用增强模式
- **高并发**：使用增强模式 + 乐观锁

### 2. 一致性级别选择
- **read_uncommitted**：性能最高，但可能脏读
- **read_committed**：平衡性能和一致性
- **serializable**：最高一致性，但性能较低

### 3. 乐观锁使用
- 在表结构中添加 `version` 字段
- 更新时检查版本号
- 失败时重试操作

### 4. 事务使用
- 相关操作使用事务
- 选择合适的隔离级别
- 避免长事务

### 5. 监控和调试
- 使用 `agent_status` 监控Agent状态
- 使用 `transaction_history` 查看操作历史
- 设置合适的日志级别

## 总结

SQLite MCP服务器提供了完整的多Agent并发控制解决方案：

1. **向后兼容**：标准模式与原来完全兼容
2. **增强功能**：支持多Agent并发控制
3. **灵活配置**：可根据需求选择不同模式
4. **完整工具集**：提供丰富的数据库操作工具
5. **监控支持**：内置状态监控和历史记录

通过合理使用这些功能，可以有效解决多Agent环境下的数据一致性问题。 