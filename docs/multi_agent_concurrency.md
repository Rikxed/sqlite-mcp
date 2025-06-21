# 多Agent并发控制方案

## 问题背景

当多个MCP Agent同时访问同一SQLite数据库时，会出现以下并发问题：

### 1. 脏读（Dirty Read）
- **场景**：Agent A读取数据时，Agent B正在修改该数据
- **问题**：Agent A可能读取到未提交的、不一致的数据
- **影响**：数据不一致，业务逻辑错误

### 2. 脏写（Dirty Write）
- **场景**：多个Agent同时修改同一数据
- **问题**：后提交的操作会覆盖先提交的操作
- **影响**：数据丢失，业务逻辑错误

### 3. 不可重复读（Non-repeatable Read）
- **场景**：同一事务内多次读取同一数据得到不同结果
- **问题**：事务期间数据被其他Agent修改
- **影响**：事务一致性被破坏

### 4. 幻读（Phantom Read）
- **场景**：同一事务内查询条件范围的数据发生变化
- **问题**：事务期间有新的数据插入或删除
- **影响**：查询结果不一致

## 解决方案

### 1. 文件锁机制（跨进程锁）

```python
import fcntl
import os

class FileLockManager:
    def __init__(self, lock_file_path: str):
        self.lock_file_path = lock_file_path
    
    def acquire_lock(self, timeout: int = 30) -> bool:
        """获取文件锁"""
        try:
            self.lock_file = open(self.lock_file_path, 'w')
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            # 等待锁释放
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    time.sleep(0.1)
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return True
                except (IOError, OSError):
                    continue
            return False
    
    def release_lock(self):
        """释放文件锁"""
        try:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
            self.lock_file.close()
        except Exception as e:
            logger.error(f"释放文件锁失败: {e}")
```

**优势：**
- 跨进程协调
- 简单可靠
- 系统级支持

**劣势：**
- 性能开销较大
- 可能产生死锁
- 粒度较粗

### 2. 乐观锁机制

```python
class OptimisticLockManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def update_with_version_check(self, query: str, params: tuple, 
                                table_name: str, record_id: int) -> bool:
        """带版本检查的更新操作"""
        try:
            # 获取当前版本
            version_query = f"SELECT version FROM {table_name} WHERE id = ?"
            current_version = self.db_manager.execute_query_with_consistency(
                version_query, (record_id,), "read_committed"
            )
            
            if not current_version:
                raise Exception(f"记录不存在: {table_name}.{record_id}")
            
            # 更新版本号
            new_version = current_version[0]["version"] + 1
            update_params = params + (new_version, record_id)
            
            # 执行更新（带乐观锁）
            affected_rows = self.db_manager.execute_update_with_optimistic_lock(
                query, update_params, "version", current_version[0]["version"]
            )
            
            return affected_rows > 0
        except Exception as e:
            logger.error(f"版本检查更新失败: {e}")
            return False
```

**优势：**
- 性能好
- 并发度高
- 无死锁风险

**劣势：**
- 需要版本字段
- 失败时需要重试
- 实现复杂

### 3. 事务隔离级别

```python
def execute_transaction_with_isolation(self, operations: List[tuple], 
                                     isolation_level: str = "serializable") -> bool:
    """执行事务（支持隔离级别）"""
    with self._write_lock:
        if not self._get_file_lock():
            raise Exception("无法获取数据库锁，操作失败")
        
        try:
            with self.get_connection() as conn:
                # 设置隔离级别
                if isolation_level == "serializable":
                    conn.execute("PRAGMA read_uncommitted = 0")
                elif isolation_level == "read_committed":
                    conn.execute("PRAGMA read_uncommitted = 0")
                else:  # read_uncommitted
                    conn.execute("PRAGMA read_uncommitted = 1")
                
                try:
                    for query, params in operations:
                        conn.execute(query, params)
                    conn.commit()
                    return True
                except Exception as e:
                    logger.error(f"事务执行失败: {e}")
                    conn.rollback()
                    return False
        finally:
            self._release_file_lock()
```

**隔离级别：**
- **READ UNCOMMITTED**：最低级别，可能发生脏读
- **READ COMMITTED**：避免脏读，可能发生不可重复读
- **SERIALIZABLE**：最高级别，完全隔离

### 4. 一致性缓存

```python
class ConsistencyManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._consistency_cache = {}
        self._cache_lock = threading.Lock()
    
    def read_with_cache_validation(self, query: str, params: tuple = (), 
                                 cache_key: Optional[str] = None) -> List[Dict]:
        """带缓存验证的读取操作"""
        if cache_key:
            with self._cache_lock:
                if cache_key in self._consistency_cache:
                    cached_result = self._consistency_cache[cache_key]
                    if self._validate_cache(cache_key, cached_result):
                        return cached_result["data"]
        
        # 执行查询
        result = self.db_manager.execute_query_with_consistency(query, params, "read_committed")
        
        # 更新缓存
        if cache_key:
            with self._cache_lock:
                self._consistency_cache[cache_key] = {
                    "data": result,
                    "timestamp": time.time(),
                    "query_hash": hashlib.md5(f"{query}{params}".encode()).hexdigest()
                }
        
        return result
```

**优势：**
- 提高读取性能
- 减少数据库压力
- 支持缓存验证

**劣势：**
- 内存占用
- 缓存一致性维护
- 实现复杂

## 实现策略

### 1. 分层锁策略

```python
class MultiAgentDatabaseManager:
    def __init__(self, db_path: str, agent_id: str):
        self.db_path = db_path
        self.agent_id = agent_id
        self._local_lock = threading.RLock()      # 本地读锁
        self._write_lock = threading.Lock()       # 本地写锁
        self._file_lock_manager = FileLockManager(f"{db_path}.lock")  # 文件锁
    
    def execute_query(self, query: str, params: tuple = (), 
                     consistency_level: str = "read_committed") -> List[Dict]:
        """执行查询"""
        with self._local_lock:  # 本地读锁
            if consistency_level == "serializable":
                # 串行化级别需要文件锁
                if not self._file_lock_manager.acquire_lock():
                    raise Exception("无法获取数据库锁")
                try:
                    return self._execute_query_internal(query, params)
                finally:
                    self._file_lock_manager.release_lock()
            else:
                return self._execute_query_internal(query, params)
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新"""
        with self._write_lock:  # 本地写锁
            if not self._file_lock_manager.acquire_lock():
                raise Exception("无法获取数据库锁")
            try:
                return self._execute_update_internal(query, params)
            finally:
                self._file_lock_manager.release_lock()
```

### 2. 事务日志记录

```python
def _log_transaction(self, operation: str, query: str, params: tuple, result: Any) -> None:
    """记录事务日志"""
    try:
        transaction = {
            "timestamp": time.time(),
            "agent_id": self.agent_id,
            "session_id": self._session_id,
            "operation": operation,
            "query": query,
            "params": params,
            "result": result
        }
        
        with open(self._transaction_log_path, 'r+') as f:
            data = json.load(f)
            data["transactions"].append(transaction)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    except Exception as e:
        logger.error(f"记录事务日志失败: {e}")
```

### 3. 超时和重试机制

```python
def execute_with_retry(self, operation, max_retries: int = 3, 
                      retry_delay: float = 0.1) -> Any:
    """带重试的操作执行"""
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if "版本冲突" in str(e) or "锁超时" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # 指数退避
                    continue
            raise e
    raise Exception(f"操作失败，已重试 {max_retries} 次")
```

## 最佳实践

### 1. 选择合适的锁策略

**读多写少的场景：**
- 使用乐观锁
- 实现缓存机制
- 设置合适的隔离级别

**写多读少的场景：**
- 使用悲观锁
- 减少锁持有时间
- 批量操作

**高并发场景：**
- 使用文件锁
- 实现队列机制
- 监控锁竞争

### 2. 性能优化

```python
# 批量操作
def batch_update(self, operations: List[tuple]) -> bool:
    """批量更新操作"""
    with self._write_lock:
        if not self._get_file_lock():
            raise Exception("无法获取数据库锁")
        try:
            with self.get_connection() as conn:
                for query, params in operations:
                    conn.execute(query, params)
                conn.commit()
                return True
        finally:
            self._release_file_lock()

# 连接池
def _init_connection_pool(self) -> None:
    """初始化连接池"""
    for _ in range(self.max_connections):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA busy_timeout = 30000")
            self._connection_pool.put(conn)
        except Exception as e:
            logger.error(f"创建连接池连接失败: {e}")
            raise
```

### 3. 监控和调试

```python
def get_agent_status(self) -> Dict[str, Any]:
    """获取Agent状态信息"""
    return {
        "agent_id": self.agent_id,
        "session_id": self._session_id,
        "database_path": self.db_path,
        "lock_file_exists": os.path.exists(self._lock_file_path),
        "transaction_log_exists": os.path.exists(self._transaction_log_path),
        "timestamp": time.time()
    }

def get_transaction_history(self, limit: int = 100) -> List[Dict]:
    """获取事务历史"""
    try:
        with open(self._transaction_log_path, 'r') as f:
            data = json.load(f)
            transactions = data.get("transactions", [])
            return transactions[-limit:] if limit > 0 else transactions
    except Exception as e:
        logger.error(f"获取事务历史失败: {e}")
        return []
```

## 总结

多Agent并发控制是一个复杂的问题，需要综合考虑：

1. **数据一致性**：确保数据的正确性和完整性
2. **性能**：在保证一致性的前提下提高并发性能
3. **可用性**：避免死锁和长时间等待
4. **可维护性**：代码清晰，易于调试和监控

通过合理使用文件锁、乐观锁、事务隔离级别和缓存机制，可以有效解决多Agent并发访问问题，确保数据的一致性和系统的稳定性。 