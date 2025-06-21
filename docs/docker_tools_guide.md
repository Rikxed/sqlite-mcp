# Docker启动后的MCP工具列表详细指南

## 概述

当前项目Docker启动后提供的是**标准模式**的SQLite MCP服务器，包含6个核心工具，支持完整的数据库操作。

## 启动方式

### 1. 构建并启动Docker容器
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 2. 查看工具列表
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | docker-compose run --rm sqlite-mcp-server
```

## 可用工具列表

### 1. sql_query - SQL查询工具

**功能**: 执行SQL查询语句，返回查询结果。支持SELECT语句，可以查询数据、统计信息等。

**参数**:
- `query` (string, 必需): SQL查询语句
- `params` (array, 可选): 查询参数列表

**使用示例**:
```bash
# 查询所有用户
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "sql_query", "arguments": {"query": "SELECT * FROM users"}}}' | docker-compose run --rm sqlite-mcp-server

# 带参数的查询
echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "sql_query", "arguments": {"query": "SELECT * FROM users WHERE age > ?", "params": ["18"]}}}' | docker-compose run --rm sqlite-mcp-server
```

**返回格式**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "查询成功，返回 3 行结果:\n[\n  {\n    \"id\": 1,\n    \"name\": \"张三\",\n    \"email\": \"zhangsan@example.com\",\n    \"age\": 25\n  }\n]"
      }
    ]
  }
}
```

---

### 2. sql_update - SQL更新工具

**功能**: 执行SQL更新语句，包括INSERT、UPDATE、DELETE操作。用于添加、修改、删除数据。

**参数**:
- `query` (string, 必需): SQL更新语句
- `params` (array, 可选): 更新参数列表

**使用示例**:
```bash
# 插入数据
echo '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "sql_update", "arguments": {"query": "INSERT INTO users (name, age, email) VALUES (?, ?, ?)", "params": ["王五", "28", "wangwu@example.com"]}}}' | docker-compose run --rm sqlite-mcp-server

# 更新数据
echo '{"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "sql_update", "arguments": {"query": "UPDATE users SET age = ? WHERE name = ?", "params": ["26", "张三"]}}}' | docker-compose run --rm sqlite-mcp-server

# 删除数据
echo '{"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "sql_update", "arguments": {"query": "DELETE FROM users WHERE name = ?", "params": ["王五"]}}}' | docker-compose run --rm sqlite-mcp-server
```

**返回格式**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "更新成功，影响 1 行"
      }
    ]
  }
}
```

---

### 3. list_tables - 列出表工具

**功能**: 列出数据库中的所有表。用于了解数据库结构。

**参数**: 无

**使用示例**:
```bash
echo '{"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "list_tables", "arguments": {}}}' | docker-compose run --rm sqlite-mcp-server
```

**返回格式**:
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "数据库中的表:\n[\n  \"users\",\n  \"products\",\n  \"orders\"\n]"
      }
    ]
  }
}
```

---

### 4. describe_table - 描述表结构工具

**功能**: 描述指定表的结构，包括列名、数据类型、约束等信息。

**参数**:
- `table_name` (string, 必需): 表名

**使用示例**:
```bash
echo '{"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "describe_table", "arguments": {"table_name": "users"}}}' | docker-compose run --rm sqlite-mcp-server
```

**返回格式**:
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "表 'users' 的结构:\n{\n  \"table_name\": \"users\",\n  \"columns\": [\n    {\n      \"cid\": 0,\n      \"name\": \"id\",\n      \"type\": \"INTEGER\",\n      \"notnull\": 0,\n      \"dflt_value\": null,\n      \"pk\": 1\n    },\n    {\n      \"cid\": 1,\n      \"name\": \"name\",\n      \"type\": \"TEXT\",\n      \"notnull\": 1,\n      \"dflt_value\": null,\n      \"pk\": 0\n    }\n  ],\n  \"create_statement\": \"CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE, age INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)\"\n}"
      }
    ]
  }
}
```

---

### 5. create_table - 创建表工具

**功能**: 创建新表。可以定义表结构、列类型、约束等。

**参数**:
- `table_name` (string, 必需): 表名
- `columns` (string, 必需): 列定义SQL语句

**使用示例**:
```bash
echo '{"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "create_table", "arguments": {"table_name": "employees", "columns": "id INTEGER PRIMARY KEY, name TEXT NOT NULL, department TEXT, salary REAL"}}}' | docker-compose run --rm sqlite-mcp-server
```

**返回格式**:
```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "表 'employees' 创建成功"
      }
    ]
  }
}
```

---

### 6. database_info - 数据库信息工具

**功能**: 获取数据库基本信息，包括表数量、数据库大小等统计信息。

**参数**: 无

**使用示例**:
```bash
echo '{"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "database_info", "arguments": {}}}' | docker-compose run --rm sqlite-mcp-server
```

**返回格式**:
```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "数据库信息:\n{\n  \"database_path\": \"/app/data/sqlite.db\",\n  \"table_count\": 3,\n  \"database_size_bytes\": 24576,\n  \"tables\": [\n    \"users\",\n    \"products\",\n    \"orders\"\n  ]\n}"
      }
    ]
  }
}
```

---

## 简化查询脚本

项目还提供了 `query.sh` 脚本，可以简化工具调用：

```bash
# 获取数据库信息
./query.sh info

# 列出所有表
./query.sh tables

# 查询所有用户
./query.sh users

# 执行自定义SQL查询
./query.sh query "SELECT * FROM products WHERE price > 100"

# 查看表结构
./query.sh describe users
```

## 错误处理

当工具执行出错时，会返回错误信息：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "错误: table 'nonexistent_table' already exists"
      }
    ],
    "isError": true
  }
}
```

## 数据库初始化

容器启动时会自动执行 `init/init.sql` 脚本，创建以下初始表和数据：

- `users` 表：用户信息
- `products` 表：产品信息  
- `orders` 表：订单信息

## 数据持久化

数据库文件存储在 `./data/sqlite.db`，通过Docker卷挂载实现数据持久化。

## 日志查看

```bash
# 查看容器日志
docker-compose logs -f sqlite-mcp-server

# 查看实时日志
docker-compose logs -f --tail=100 sqlite-mcp-server
```

## 性能特点

- **单线程安全**: 适合单Agent使用
- **WAL模式**: SQLite使用WAL模式提高并发性能
- **连接池**: 自动管理数据库连接
- **参数化查询**: 防止SQL注入攻击 