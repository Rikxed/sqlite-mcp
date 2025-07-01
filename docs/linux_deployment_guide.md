# Linux服务器部署指南

## 概述

本指南介绍如何在Linux服务器上部署SQLite MCP服务器，并解决常见的服务检查超时问题。

## 部署步骤

### 1. 环境准备

```bash
# 安装Docker和Docker Compose
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到docker组（可选）
sudo usermod -aG docker $USER
```

### 2. 项目部署

```bash
# 克隆项目
git clone https://github.com/Rikxed/sqlite-mcp.git
cd sqlite-mcp

# 构建并启动服务
docker-compose up -d --build
```

### 3. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 查看容器日志
docker-compose logs -f sqlite-mcp-server

# 检查健康状态
docker-compose exec sqlite-mcp-server python health_check.py
```

## 常见问题解决

### 问题1: Service check timed out

**错误信息**: `Service check timed out. Please verify if the Docker MCP service is available`

**原因分析**:
1. 服务启动时间过长
2. 健康检查配置不当
3. 数据库初始化失败
4. 网络连接问题

**解决方案**:

#### 方案1: 调整健康检查配置

```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD", "python", "health_check.py"]
  interval: 30s      # 检查间隔
  timeout: 15s       # 超时时间
  retries: 3         # 重试次数
  start_period: 90s  # 启动等待时间
```

#### 方案2: 手动验证服务状态

```bash
# 进入容器检查
docker-compose exec sqlite-mcp-server bash

# 检查Python环境
python --version

# 检查数据库连接
python -c "from database.connection import db_manager; print('Database OK')"

# 检查MCP服务器
python -c "from mcp.enhanced_server import create_enhanced_server; print('MCP Server OK')"
```

#### 方案3: 增加启动等待时间

```bash
# 修改启动脚本，增加等待时间
echo "🔍 等待服务启动完成..."
sleep 10  # 增加等待时间
```

### 问题2: 数据库初始化失败

**解决方案**:
```bash
# 检查数据库文件权限
sudo chown -R $USER:$USER ./data

# 重新初始化数据库
docker-compose down
rm -rf ./data/*
docker-compose up -d
```

### 问题3: 端口冲突

**解决方案**:
```bash
# 检查端口占用
sudo netstat -tlnp | grep :80

# 修改端口映射（如果需要）
# 在docker-compose.yml中添加ports配置
```

## 监控和维护

### 1. 日志监控

```bash
# 实时查看日志
docker-compose logs -f sqlite-mcp-server

# 查看错误日志
docker-compose logs sqlite-mcp-server | grep ERROR
```

### 2. 性能监控

```bash
# 查看容器资源使用
docker stats sqlite-mcp-server

# 查看磁盘使用
docker system df
```

### 3. 自动重启

```bash
# 设置自动重启策略
# 在docker-compose.yml中已配置: restart: unless-stopped
```

## 故障排除

### 1. 服务无法启动

```bash
# 检查Docker服务状态
sudo systemctl status docker

# 检查容器日志
docker-compose logs sqlite-mcp-server

# 重新构建镜像
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 2. 健康检查失败

```bash
# 手动运行健康检查
docker-compose exec sqlite-mcp-server python health_check.py

# 检查依赖
docker-compose exec sqlite-mcp-server pip list

# 检查Python路径
docker-compose exec sqlite-mcp-server python -c "import sys; print(sys.path)"
```

### 3. 数据库连接问题

```bash
# 检查数据库文件
ls -la ./data/

# 检查数据库内容
docker-compose exec sqlite-mcp-server sqlite3 /app/data/restaurants.db ".tables"
```

## 最佳实践

### 1. 环境变量配置

```bash
# 创建环境变量文件
cat > .env << EOF
DATABASE_PATH=/app/data/restaurants.db
LOG_LEVEL=INFO
PYTHONPATH=/app
EOF
```

### 2. 数据备份

```bash
# 备份数据库
docker-compose exec sqlite-mcp-server sqlite3 /app/data/restaurants.db ".backup /app/data/backup.db"

# 备份整个数据目录
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz ./data/
```

### 3. 安全配置

```bash
# 设置文件权限
chmod 600 .env
chmod 755 ./data

# 限制容器资源
# 在docker-compose.yml中添加资源限制
```

## 联系支持

如果遇到其他问题，请：

1. 查看详细日志: `docker-compose logs sqlite-mcp-server`
2. 运行健康检查: `docker-compose exec sqlite-mcp-server python health_check.py`
3. 提交Issue到GitHub仓库
4. 提供错误信息和系统环境信息 