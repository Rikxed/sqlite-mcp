# 标准MCP协议使用指南

## 📋 概述

本项目现在支持完整的标准MCP协议 (2024-11-05)，提供了与MCP客户端完全兼容的接口。

## 🚀 快速开始

### 启动标准MCP服务器

```bash
# 使用Docker启动
docker-compose up -d

# 或者直接运行Python
python main_standard.py
```

### 测试标准MCP协议

```bash
python test_standard_mcp.py
```

## 📡 协议支持

### 必需方法

| 方法 | 描述 | 状态 |
|------|------|------|
| `initialize` | 初始化连接 | ✅ 已实现 |
| `tools/list` | 列出工具 | ✅ 已实现 |
| `tools/call` | 调用工具 | ✅ 已实现 |
| `notifications/list` | 列出通知 | ✅ 已实现 |
| `resources/list` | 列出资源 | ✅ 已实现 |
| `resources/read` | 读取资源 | ✅ 已实现 |

### 协议版本
- **当前版本**: `2024-11-05`
- **服务器名称**: `sqlite-mcp-server`
- **服务器版本**: `1.0.0`

## 🛠️ 可用工具

### 1. SQL查询 (`sql_query`)
执行SQL查询语句，返回查询结果。

**参数**:
- `query` (string): SQL查询语句
- `params` (array): 查询参数列表

**示例**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "sql_query",
    "arguments": {
      "query": "SELECT * FROM restaurants WHERE name LIKE ?",
      "params": ["%早茶%"]
    }
  }
}
```

### 2. SQL更新 (`sql_update`)
执行SQL更新语句，包括INSERT、UPDATE、DELETE操作。

**参数**:
- `query` (string): SQL更新语句
- `params` (array): 更新参数列表

**示例**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "sql_update",
    "arguments": {
      "query": "UPDATE time_slots SET available = available - 1 WHERE id = ?",
      "params": ["123"]
    }
  }
}
```

### 3. 预订餐桌 (`book_table`)
预订餐桌，减少指定时段的可用数量。

**参数**:
- `restaurant_name` (string): 餐厅名称
- `capacity` (integer): 桌型容量
- `slot_start` (string): 开始时间
- `quantity` (integer): 预订数量 (默认: 1)

**示例**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "book_table",
    "arguments": {
      "restaurant_name": "广式早茶",
      "capacity": 4,
      "slot_start": "2025-06-25 11:00:00",
      "quantity": 1
    }
  }
}
```

## 🔔 通知

| 通知名称 | 描述 |
|----------|------|
| `database_changed` | 数据库发生变化时的通知 |
| `booking_created` | 预订创建成功的通知 |

## 📁 资源

| 资源名称 | URI | 描述 | MIME类型 |
|----------|-----|------|----------|
| `restaurants` | `sqlite:///restaurants` | 餐厅信息 | `application/json` |
| `time_slots` | `sqlite:///time_slots` | 时段库存信息 | `application/json` |

## 📝 使用示例

### 1. 初始化连接

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "my-client",
      "version": "1.0.0"
    }
  }
}
```

### 2. 获取工具列表

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

### 3. 查询餐厅信息

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "sql_query",
    "arguments": {
      "query": "SELECT * FROM restaurants"
    }
  }
}
```

### 4. 读取资源

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/read",
  "params": {
    "uri": "sqlite:///restaurants"
  }
}
```

## 🔧 错误处理

服务器遵循标准JSON-RPC 2.0错误码：

| 错误码 | 描述 |
|--------|------|
| -32002 | Server not initialized |
| -32601 | Method not found |
| -32603 | Internal error |
| -32700 | Parse error |

## 🐳 Docker使用

### 启动服务
```bash
docker-compose up -d
```

### 查看日志
```bash
docker-compose logs -f sqlite-mcp-server
```

### 停止服务
```bash
docker-compose down
```

## 🧪 测试

运行完整测试套件：

```bash
python test_standard_mcp.py
```

测试包括：
- ✅ 初始化测试
- ✅ 工具列表测试
- ✅ 通知列表测试
- ✅ 资源列表测试
- ✅ SQL查询测试
- ✅ 预订餐桌测试
- ✅ 资源读取测试

## 📊 与简化版MCP的差异

| 特性 | 简化版MCP | 标准MCP |
|------|-----------|---------|
| 协议版本 | 无 | 2024-11-05 |
| 初始化方法 | ❌ | ✅ |
| 通知支持 | ❌ | ✅ |
| 资源支持 | ❌ | ✅ |
| 错误处理 | 基础 | 完整 |
| 客户端兼容性 | 有限 | 完全兼容 |

## 🎯 下一步

1. **扩展工具**: 添加更多业务相关的工具
2. **通知实现**: 实现实时通知功能
3. **资源扩展**: 添加更多数据资源
4. **性能优化**: 优化查询和响应性能
5. **安全增强**: 添加认证和授权机制 