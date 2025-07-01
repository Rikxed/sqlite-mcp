# MCP客户端连接指南

## 问题诊断结果

经过诊断，**Docker中的MCP服务器完全正常工作**，所有MCP协议功能都已正确实现：

✅ **初始化连接** - 正常  
✅ **工具列表** - 10个工具可用  
✅ **工具调用** - 正常工作  
✅ **关闭连接** - 正常  

## 可能的问题原因

如果官方MCP客户端仍然无法连接，可能的原因包括：

### 1. 客户端配置问题

**检查客户端配置文件**，确保正确配置了Docker容器：

```json
{
  "mcpServers": {
    "sqlite-server": {
      "command": "docker-compose",
      "args": ["exec", "-T", "sqlite-mcp-server", "python", "main_enhanced.py"],
      "cwd": "/path/to/your/project/db"
    }
  }
}
```

### 2. 网络连接问题

**检查网络配置**：
- 确保Docker容器正在运行
- 检查防火墙设置
- 验证网络连接

### 3. 客户端版本兼容性

**检查客户端版本**：
- 确保使用支持MCP协议 2024-11-05 的客户端版本
- 检查客户端是否支持stdio模式

### 4. 认证或权限问题

**检查权限设置**：
- 确保客户端有权限执行docker-compose命令
- 检查Docker权限

## 解决方案

### 方案1：使用Docker Compose直接连接

```bash
# 1. 确保容器正在运行
docker-compose ps

# 2. 测试连接
docker-compose exec -T sqlite-mcp-server python main_enhanced.py
```

### 方案2：使用Docker命令连接

```bash
# 1. 获取容器ID
docker ps

# 2. 直接连接
docker exec -i <container_id> python main_enhanced.py
```

### 方案3：端口转发（如果需要）

如果客户端不支持stdio模式，可以考虑添加HTTP模式：

```yaml
# docker-compose.yml 添加端口映射
services:
  sqlite-mcp-server:
    ports:
      - "8080:8080"
```

## 测试连接

使用提供的测试脚本验证连接：

```bash
python3 test_mcp_client_connection.py
```

## 常见错误及解决方案

### 错误1：Method not found
**原因**：客户端发送了服务器不支持的方法
**解决**：已修复，现在支持所有标准MCP方法

### 错误2：Connection timeout
**原因**：网络连接问题或容器未启动
**解决**：
```bash
# 检查容器状态
docker-compose ps

# 重启容器
docker-compose restart
```

### 错误3：Permission denied
**原因**：Docker权限问题
**解决**：
```bash
# 添加用户到docker组
sudo usermod -aG docker $USER

# 重新登录或重启
```

## 客户端配置示例

### VS Code MCP扩展配置

```json
{
  "mcp.servers": {
    "sqlite-server": {
      "command": "docker-compose",
      "args": ["exec", "-T", "sqlite-mcp-server", "python", "main_enhanced.py"],
      "cwd": "/Users/yaolu/Desktop/gmeeai/db"
    }
  }
}
```

### 其他MCP客户端配置

根据具体客户端的要求，配置命令和参数：

```json
{
  "server": {
    "name": "sqlite-mcp-server",
    "command": "docker-compose",
    "args": ["exec", "-T", "sqlite-mcp-server", "python", "main_enhanced.py"],
    "workingDirectory": "/Users/yaolu/Desktop/gmeeai/db"
  }
}
```

## 可用工具列表

服务器提供以下10个工具：

1. **sql_query** - 执行SQL查询语句
2. **sql_update** - 执行SQL更新语句
3. **sql_transaction** - 执行事务操作
4. **natural_language_query** - 自然语言数据库操作
5. **list_tables** - 列出数据库表
6. **describe_table** - 描述表结构
7. **create_table** - 创建新表
8. **database_info** - 获取数据库信息
9. **agent_status** - 获取Agent状态
10. **transaction_history** - 获取事务历史

## 联系支持

如果问题仍然存在，请提供：

1. 客户端类型和版本
2. 错误日志
3. 客户端配置文件
4. 操作系统信息

这样我可以提供更具体的解决方案。 