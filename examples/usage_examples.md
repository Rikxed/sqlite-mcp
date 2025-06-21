# SQLite MCP服务器使用示例

## 基本操作示例

### 1. 创建用户表

```json
{
  "name": "create_table",
  "arguments": {
    "table_name": "users",
    "columns": "id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE, age INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
  }
}
```

### 2. 插入用户数据

```json
{
  "name": "execute_update",
  "arguments": {
    "query": "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
    "params": ["张三", "zhangsan@example.com", "25"]
  }
}
```

### 3. 查询用户数据

```json
{
  "name": "execute_query",
  "arguments": {
    "query": "SELECT * FROM users WHERE age > ?",
    "params": ["20"]
  }
}
```

### 4. 更新用户数据

```json
{
  "name": "execute_update",
  "arguments": {
    "query": "UPDATE users SET age = ? WHERE name = ?",
    "params": ["26", "张三"]
  }
}
```

### 5. 删除用户数据

```json
{
  "name": "execute_update",
  "arguments": {
    "query": "DELETE FROM users WHERE name = ?",
    "params": ["张三"]
  }
}
```

### 6. 列出所有表

```json
{
  "name": "list_tables",
  "arguments": {}
}
```

### 7. 查看表结构

```json
{
  "name": "describe_table",
  "arguments": {
    "table_name": "users"
  }
}
```

## 复杂查询示例

### 1. 多表连接查询

```json
{
  "name": "execute_query",
  "arguments": {
    "query": "SELECT u.name, p.title FROM users u JOIN posts p ON u.id = p.user_id WHERE u.age > ?",
    "params": ["25"]
  }
}
```

### 2. 聚合查询

```json
{
  "name": "execute_query",
  "arguments": {
    "query": "SELECT age, COUNT(*) as count FROM users GROUP BY age ORDER BY age"
  }
}
```

### 3. 子查询

```json
{
  "name": "execute_query",
  "arguments": {
    "query": "SELECT * FROM users WHERE age > (SELECT AVG(age) FROM users)"
  }
}
```

## 批量操作示例

### 1. 批量插入

```json
{
  "name": "execute_update",
  "arguments": {
    "query": "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
    "params": ["李四", "lisi@example.com", "30"]
  }
}
```

然后继续插入更多数据...

### 2. 条件更新

```json
{
  "name": "execute_update",
  "arguments": {
    "query": "UPDATE users SET age = age + 1 WHERE age < ?",
    "params": ["30"]
  }
}
```

## 错误处理示例

### 1. 表不存在错误

```json
{
  "name": "execute_query",
  "arguments": {
    "query": "SELECT * FROM non_existent_table"
  }
}
```

预期返回错误信息。

### 2. 语法错误

```json
{
  "name": "execute_update",
  "arguments": {
    "query": "INSERT INTO users VALUES (invalid_syntax)"
  }
}
```

预期返回SQL语法错误信息。

## 最佳实践

1. **使用参数化查询**: 始终使用 `?` 占位符和 `params` 参数来防止SQL注入
2. **错误处理**: 检查返回的 `isError` 字段来处理错误情况
3. **事务管理**: 对于复杂操作，考虑使用事务来确保数据一致性
4. **性能优化**: 对于大量数据操作，考虑使用批量操作
5. **安全性**: 避免在查询中直接拼接用户输入

## 常见问题

### Q: 如何处理中文数据？
A: 服务器支持UTF-8编码，可以直接处理中文字符。

### Q: 如何备份数据库？
A: 数据库文件位于 `data/sqlite.db`，可以直接复制备份。

### Q: 如何查看执行日志？
A: 使用 `docker-compose logs -f` 查看实时日志。

### Q: 如何修改数据库路径？
A: 通过环境变量 `DATABASE_PATH` 或修改 `.env` 文件。 