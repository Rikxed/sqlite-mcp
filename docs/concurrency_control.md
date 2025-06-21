# 并发控制机制

## 概述

本文档详细说明了SQLite MCP服务器如何处理多线程并发读写问题，包括当前实现的机制和最佳实践。

## 当前版本的并发控制机制

### 1. SQLite WAL模式

当前版本使用SQLite的WAL（Write-Ahead Logging）模式来处理并发访问：

```python
def _init_database(self) -> None:
    """初始化数据库连接"""
    try:
        with self.get_connection() as conn:
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            # 设置WAL模式以提高并发性能
            conn.execute("PRAGMA journal_mode = WAL")
            logger.info("数据库初始化完成")
```

**WAL模式的优势：**
- **读操作不阻塞写操作**：多个读操作可以与一个写操作并发进行
- **写操作不阻塞读操作**：写操作不会阻塞正在进行的读操作
- **提高并发性能**：显著提高了多线程环境下的性能
- **数据一致性**：保证数据的一致性和完整性

### 2. 单线程事件循环架构

MCP服务器采用异步单线程架构：

```python
async def run(self):
    """运行服务器 - 标准stdio模式"""
    while True:
        try:
            # 从标准输入读取请求
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            request = json.loads(line.strip())
            response = await self.handle_request(request)
            
            # 输出响应到标准输出
            print(json.dumps(response, ensure_ascii=False))
            sys.stdout.flush()
```

**单线程架构的优势：**
- **避免竞争条件**：所有数据库操作都在同一个事件循环中串行执行
- **简化并发控制**：不需要复杂的锁机制
- **天然线程安全**：避免了多线程间的数据竞争

### 3. 连接池模式

每次数据库操作都创建新的连接：

```python
@contextmanager
def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
    """获取数据库连接的上下文管理器"""
    conn = None
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        yield conn
    except Exception as e:
        logger.error(f"数据库连接错误: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
```

**连接池模式的优势：**
- **避免连接共享**：每个操作都有独立的连接
- **自动资源管理**：连接自动创建和释放
- **避免死锁**：不会出现连接死锁问题

## 线程安全版本

为了支持真正的多线程环境，我们提供了线程安全的数据库管理器：

### 1. 连接池管理

```python
class ThreadSafeDatabaseManager:
    def __init__(self, db_path: Optional[str] = None, max_connections: int = 10):
        self._connection_pool = Queue(maxsize=max_connections)
        self._lock = threading.RLock()  # 可重入锁
        self._write_lock = threading.Lock()  # 写操作专用锁
```

### 2. 读写锁分离

```python
def execute_query(self, query: str, params: tuple = ()) -> list:
    """执行查询语句（线程安全）"""
    with self._lock:  # 读操作使用可重入锁
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

def execute_update(self, query: str, params: tuple = ()) -> int:
    """执行更新语句（线程安全）"""
    with self._write_lock:  # 写操作使用专用锁
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
```

### 3. 事务支持

```python
def execute_transaction(self, operations: list) -> bool:
    """执行事务（线程安全）"""
    with self._write_lock:  # 事务使用写锁
        with self.get_connection() as conn:
            try:
                for query, params in operations:
                    conn.execute(query, params)
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"事务执行失败: {e}")
                conn.rollback()
                return False
```

## 并发控制策略

### 1. 读操作并发控制

- **多个读操作可以并发执行**
- **使用可重入锁（RLock）**：允许同一线程多次获取锁
- **不阻塞其他读操作**

### 2. 写操作并发控制

- **写操作使用专用锁**：确保同一时间只有一个写操作
- **写操作会阻塞其他写操作**
- **写操作不会阻塞读操作**（WAL模式）

### 3. 事务并发控制

- **事务使用写锁**：确保事务的原子性
- **支持复杂事务操作**
- **自动回滚机制**

## 性能优化

### 1. SQLite配置优化

```python
# 设置超时时间
conn.execute("PRAGMA busy_timeout = 30000")  # 30秒超时
# 设置缓存大小
conn.execute("PRAGMA cache_size = -64000")  # 64MB缓存
```

### 2. 连接池优化

- **预创建连接**：避免运行时创建连接的开销
- **连接复用**：减少连接创建和销毁的开销
- **超时控制**：避免无限等待

### 3. 锁策略优化

- **读写锁分离**：提高并发性能
- **细粒度锁**：减少锁竞争
- **超时机制**：避免死锁

## 使用示例

### 1. 基本并发操作

```python
from database.connection import thread_safe_db_manager
import threading

def read_operation():
    result = thread_safe_db_manager.execute_query("SELECT * FROM users")
    print(f"读取到 {len(result)} 个用户")

def write_operation():
    affected = thread_safe_db_manager.execute_update(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        ("新用户", "new@example.com")
    )
    print(f"插入了 {affected} 行数据")

# 并发执行
threads = [
    threading.Thread(target=read_operation),
    threading.Thread(target=write_operation),
    threading.Thread(target=read_operation)
]

for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
```

### 2. 事务操作

```python
def complex_transaction():
    operations = [
        ("INSERT INTO users (name, email) VALUES (?, ?)", ("用户1", "user1@example.com")),
        ("INSERT INTO products (name, price) VALUES (?, ?)", ("产品1", 100.0)),
        ("INSERT INTO orders (user_id, product_id) VALUES (?, ?)", (1, 1))
    ]
    
    success = thread_safe_db_manager.execute_transaction(operations)
    return success
```

## 最佳实践

### 1. 选择合适的数据库管理器

- **单线程环境**：使用 `DatabaseManager`
- **多线程环境**：使用 `ThreadSafeDatabaseManager`

### 2. 合理使用事务

- **批量操作**：使用事务提高性能
- **数据一致性**：使用事务保证数据完整性
- **避免长事务**：减少锁持有时间

### 3. 连接池配置

- **合理设置连接数**：根据并发需求调整
- **监控连接使用**：避免连接池耗尽
- **及时释放连接**：使用上下文管理器

### 4. 错误处理

- **捕获异常**：正确处理数据库异常
- **重试机制**：对于临时错误实现重试
- **日志记录**：记录详细的错误信息

## 监控和调试

### 1. 性能监控

```python
import time

def benchmark_operation():
    start_time = time.time()
    # 执行数据库操作
    result = thread_safe_db_manager.execute_query("SELECT COUNT(*) FROM users")
    end_time = time.time()
    print(f"操作耗时: {end_time - start_time:.3f}秒")
```

### 2. 连接池监控

```python
def monitor_connection_pool():
    pool_size = thread_safe_db_manager._connection_pool.qsize()
    max_size = thread_safe_db_manager.max_connections
    print(f"连接池使用率: {pool_size}/{max_size}")
```

### 3. 锁竞争监控

```python
import threading

def monitor_lock_contention():
    # 监控锁的获取和释放
    print(f"当前活跃线程数: {threading.active_count()}")
```

## 总结

当前版本的SQLite MCP服务器通过以下机制有效避免了多线程并发读写问题：

1. **WAL模式**：提供读写的并发支持
2. **单线程架构**：避免多线程竞争
3. **连接池**：管理数据库连接
4. **锁机制**：控制并发访问
5. **事务支持**：保证数据一致性

这些机制确保了在高并发环境下的数据安全性和系统稳定性。 