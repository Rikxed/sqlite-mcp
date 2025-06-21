# SQLite MCP 服务器

一个基于Python实现的SQLite标准MCP（Model Context Protocol）服务器，支持数据库的读写操作，使用Docker进行容器化部署，以stdio模式运行，支持自然语言交互。

## 功能特性

- 🔍 **SQL查询执行**: 支持SELECT查询语句
- ✏️ **数据更新操作**: 支持INSERT、UPDATE、DELETE语句
- 📋 **表管理**: 列出所有表、查看表结构、创建新表
- 🗣️ **自然语言交互**: 支持中文自然语言建表和查询
- 🔒 **并发控制**: 支持多Agent并发访问和事务管理
- 🐳 **Docker部署**: 完整的容器化支持
- ⚙️ **配置管理**: 灵活的环境变量配置
- 📝 **日志记录**: 完整的操作日志记录
- 🧪 **测试覆盖**: 完整的测试和演示脚本
- 🌐 **stdio模式**: 标准MCP协议，支持自然语言交互
- 📋 **初始化脚本**: 支持配置文件方式启动和初始化
- 🚀 **一键启动**: Docker拉起即可使用，无需额外脚本

## 项目结构

```
db/
├── config/                 # 配置模块
│   ├── __init__.py
│   ├── settings.py        # 应用配置
│   └── example.env        # 示例环境配置
├── database/              # 数据库模块
│   ├── __init__.py
│   ├── connection.py      # 数据库连接管理
│   ├── advanced_connection.py  # 高级连接管理
│   └── multi_agent_manager.py  # 多Agent管理器
├── mcp/                   # MCP服务器模块
│   ├── __init__.py
│   ├── server.py          # 标准MCP服务器实现
│   ├── simple_server.py   # 简化MCP服务器实现
│   ├── enhanced_server.py # 增强版MCP服务器（支持并发）
│   └── natural_language_server.py # 自然语言MCP服务器
├── init/                  # 初始化脚本
│   └── init.sql          # 数据库初始化SQL脚本
├── examples/              # 使用示例
│   ├── usage_examples.md  # 详细使用示例
│   ├── concurrent_usage_example.py # 并发使用示例
│   ├── multi_agent_concurrency_example.py # 多Agent并发示例
│   └── natural_language_example.py # 自然语言使用示例
├── docs/                  # 文档
│   ├── usage_guide.md     # 使用指南
│   ├── concurrency_control.md # 并发控制文档
│   ├── multi_agent_concurrency.md # 多Agent并发文档
│   └── natural_language_usage.md # 自然语言使用指南
├── data/                  # 数据目录（Docker卷挂载）
├── main.py               # 主程序入口 (stdio模式)
├── main_enhanced.py      # 增强版主程序（支持并发）
├── main_natural_language.py # 自然语言主程序
├── test_server.py        # 测试脚本
├── test_stdio.py         # stdio模式测试脚本
├── demo.py               # 演示脚本
├── query.sh              # 简化查询脚本
├── requirements.txt      # Python依赖
├── Dockerfile           # Docker镜像配置
├── docker-compose.yml   # Docker Compose配置
├── .gitignore           # Git忽略文件
├── .dockerignore        # Docker忽略文件
└── README.md            # 项目说明
```

## 快速开始

### 方法1: Docker启动（推荐）

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd db
   ```

2. **启动服务器**
   ```bash
   # 标准模式
   docker-compose up --build
   
   # 增强模式（支持并发）
   docker-compose -f docker-compose.yml up --build enhanced
   
   # 自然语言模式
   docker-compose -f docker-compose.yml up --build natural-language
   ```

3. **服务器将自动初始化数据库并进入stdio模式**

### 方法2: 本地启动

```bash
# 标准模式
python main.py

# 增强模式（支持并发）
python main_enhanced.py

# 自然语言模式
python main_natural_language.py
```

### 方法3: 直接Docker调用

```bash
# 构建镜像
docker-compose build

# 查询数据库信息
./query.sh info

# 查询所有用户
./query.sh users

# 执行自定义查询
./query.sh query "SELECT * FROM products"
```

### 方法4: 本地开发

1. **创建虚拟环境**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行测试**
   ```bash
   python test_server.py
   ```

## 服务器模式

### 1. 标准模式 (main.py)
- 基本的SQL操作
- 单线程安全
- 适合单Agent使用

### 2. 增强模式 (main_enhanced.py)
- 支持多Agent并发
- 事务管理和乐观锁
- 一致性控制
- 适合多Agent协作

### 3. 自然语言模式 (main_natural_language.py)
- 支持中文自然语言建表
- 自然语言查询和更新
- 自动SQL生成
- 适合非技术用户

## 自然语言功能

### 自然语言建表
```bash
# 使用自然语言创建表
描述: "创建一个用户表，包含姓名、年龄、邮箱字段"
```

生成的SQL:
```sql
CREATE TABLE 用户 (姓名 TEXT, 年龄 INTEGER, 邮箱 TEXT)
```

### 自然语言查询
```bash
# 使用自然语言查询
描述: "查询所有年龄大于18的用户"
```

生成的SQL:
```sql
SELECT * FROM users WHERE age > 18
```

### 自然语言插入
```bash
# 使用自然语言插入数据
描述: "向用户表插入一个叫张三的用户，年龄25岁"
```

生成的SQL:
```sql
INSERT INTO users (name, age) VALUES ('张三', 25)
```

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DATABASE_PATH` | `data/sqlite.db` | 数据库文件路径 |
| `INIT_SCRIPT` | `init/init.sql` | 初始化SQL脚本路径 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `AGENT_ID` | 自动生成 | Agent唯一标识符 |
| `USE_THREAD_SAFE` | `false` | 是否使用线程安全模式 |

### 初始化脚本

服务器启动时会自动执行 `init/init.sql` 脚本，用于：
- 创建数据库表结构
- 插入初始数据
- 设置数据库约束

示例初始化脚本：
```sql
-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入示例数据
INSERT OR IGNORE INTO users (id, name, email, age) VALUES 
(1, '张三', 'zhangsan@example.com', 25);
```

## 使用方法

### 简化查询脚本

使用 `query.sh` 脚本进行快速查询：

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

### 直接Docker调用

```bash
# 基本格式
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "工具名", "arguments": {参数}}}' | docker run --rm -i -v $(pwd)/data:/app/data -v $(pwd)/config:/app/config -v $(pwd)/init:/app/init -e DATABASE_PATH=/app/data/sqlite.db -e INIT_SCRIPT=/app/init/init.sql db-sqlite-mcp-server
```

## MCP工具说明

### 标准模式工具

#### 1. sql_query
执行SQL查询语句，返回查询结果。

**参数:**
- `query` (string, 必需): SQL查询语句
- `params` (array, 可选): 查询参数列表

**示例:**
```json
{
  "query": "SELECT * FROM users WHERE age > ?",
  "params": ["18"]
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
  "query": "INSERT INTO users (name, age) VALUES (?, ?)",
  "params": ["张三", "25"]
}
```

#### 3. list_tables
列出数据库中的所有表。

**参数:** 无

#### 4. describe_table
描述指定表的结构。

**参数:**
- `table_name` (string, 必需): 表名

#### 5. create_table
创建新表。

**参数:**
- `table_name` (string, 必需): 表名
- `columns` (string, 必需): 列定义SQL语句

#### 6. database_info
获取数据库基本信息。

**参数:** 无

### 增强模式工具

除了标准工具外，还包含：

#### 7. sql_transaction
执行事务操作。

**参数:**
- `operations` (array, 必需): 操作列表
- `isolation_level` (string, 可选): 隔离级别

#### 8. agent_status
获取当前Agent状态。

**参数:** 无

#### 9. transaction_history
获取事务历史记录。

**参数:**
- `limit` (integer, 可选): 返回记录数量限制

### 自然语言模式工具

#### 10. natural_language_query
使用自然语言进行查询。

**参数:**
- `description` (string, 必需): 自然语言查询描述

#### 11. natural_language_create_table
使用自然语言创建表。

**参数:**
- `description` (string, 必需): 自然语言表结构描述

#### 12. natural_language_insert
使用自然语言插入数据。

**参数:**
- `description` (string, 必需): 自然语言插入描述

#### 13. natural_language_update
使用自然语言更新数据。

**参数:**
- `description` (string, 必需): 自然语言更新描述

## 并发控制

### 多Agent并发
- 支持多个MCP Agent同时访问数据库
- 使用文件锁和事务管理确保数据一致性
- 支持乐观锁和悲观锁机制

### 事务隔离
- 支持不同的事务隔离级别
- 防止脏读、不可重复读和幻读
- 自动冲突检测和解决

## 开发指南

### 添加新工具
1. 在对应的服务器类中添加工具定义
2. 实现工具的处理方法
3. 在 `_call_tool` 方法中添加路由

### 扩展自然语言功能
1. 在 `natural_language_server.py` 中添加新的解析方法
2. 更新字段类型映射
3. 添加相应的测试用例

## 测试

### 运行测试
```bash
# 标准模式测试
python test_server.py

# 自然语言功能测试
python examples/natural_language_example.py

# 并发功能测试
python examples/multi_agent_concurrency_example.py
```

### 测试覆盖
- 基本SQL操作
- 自然语言解析
- 并发控制
- 错误处理
- 性能测试

## 部署

### Docker部署
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 生产环境
- 使用持久化存储
- 配置日志轮转
- 设置监控告警
- 定期备份数据

## 贡献

欢迎提交Issue和Pull Request！

### 开发环境设置
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

MIT License

## 更新日志

### v2.0.0
- 添加自然语言建表功能
- 支持多Agent并发控制
- 增强事务管理
- 改进错误处理

### v1.0.0
- 基础SQLite MCP服务器
- Docker容器化支持
- 基本CRUD操作 