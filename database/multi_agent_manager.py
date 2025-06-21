"""
多Agent数据库管理器 - 解决多MCP Agent并发访问问题
"""
import sqlite3
import logging
import threading
import fcntl
import os
import time
import uuid
from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any, List
from pathlib import Path
import json
import hashlib

from config.settings import settings

logger = logging.getLogger(__name__)


class MultiAgentDatabaseManager:
    """多Agent数据库管理器 - 支持跨进程并发控制"""
    
    def __init__(self, db_path: Optional[str] = None, agent_id: Optional[str] = None):
        """
        初始化多Agent数据库管理器
        
        Args:
            db_path: 数据库文件路径
            agent_id: Agent唯一标识符
        """
        self.db_path = db_path or settings.database_path
        self.agent_id = agent_id or str(uuid.uuid4())
        self._lock_file_path = f"{self.db_path}.lock"
        self._transaction_log_path = f"{self.db_path}.transactions"
        self._session_id = str(uuid.uuid4())
        self._local_lock = threading.RLock()
        self._write_lock = threading.Lock()
        self._ensure_data_directory()
        self._init_database()
        self._init_transaction_log()
        logger.info(f"多Agent数据库管理器初始化完成 - Agent ID: {self.agent_id}")
    
    def _ensure_data_directory(self) -> None:
        """确保数据目录存在"""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"数据库路径: {self.db_path}")
    
    def _init_database(self) -> None:
        """初始化数据库连接"""
        try:
            with self.get_connection() as conn:
                # 启用外键约束
                conn.execute("PRAGMA foreign_keys = ON")
                # 设置WAL模式以提高并发性能
                conn.execute("PRAGMA journal_mode = WAL")
                # 设置超时时间
                conn.execute("PRAGMA busy_timeout = 60000")  # 60秒超时
                # 设置缓存大小
                conn.execute("PRAGMA cache_size = -128000")  # 128MB缓存
                # 设置同步模式
                conn.execute("PRAGMA synchronous = NORMAL")
                # 设置临时存储
                conn.execute("PRAGMA temp_store = MEMORY")
                logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _init_transaction_log(self) -> None:
        """初始化事务日志"""
        try:
            if not os.path.exists(self._transaction_log_path):
                with open(self._transaction_log_path, 'w') as f:
                    json.dump({"transactions": []}, f)
        except Exception as e:
            logger.error(f"初始化事务日志失败: {e}")
    
    def _get_file_lock(self, timeout: int = 30) -> bool:
        """获取文件锁（跨进程锁）"""
        try:
            self._lock_file = open(self._lock_file_path, 'w')
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            logger.warning(f"Agent {self.agent_id} 无法获取文件锁，等待中...")
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    time.sleep(0.1)
                    fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return True
                except (IOError, OSError):
                    continue
            logger.error(f"Agent {self.agent_id} 获取文件锁超时")
            return False
    
    def _release_file_lock(self) -> None:
        """释放文件锁"""
        try:
            if hasattr(self, '_lock_file'):
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
                self._lock_file.close()
        except Exception as e:
            logger.error(f"释放文件锁失败: {e}")
    
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
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        获取数据库连接的上下文管理器（多Agent安全）
        
        Yields:
            sqlite3.Connection: 数据库连接对象
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            # 设置连接参数
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA busy_timeout = 60000")
            yield conn
        except Exception as e:
            logger.error(f"数据库连接错误: {e}")
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query_with_consistency(self, query: str, params: tuple = (), 
                                     consistency_level: str = "read_committed") -> List[Dict]:
        """
        执行查询语句（支持一致性级别）
        
        Args:
            query: SQL查询语句
            params: 查询参数
            consistency_level: 一致性级别 ("read_uncommitted", "read_committed", "serializable")
            
        Returns:
            list: 查询结果列表
        """
        with self._local_lock:
            if consistency_level == "serializable":
                # 串行化级别：获取文件锁确保一致性
                if not self._get_file_lock():
                    raise Exception("无法获取数据库锁，操作失败")
                try:
                    with self.get_connection() as conn:
                        cursor = conn.execute(query, params)
                        results = [dict(row) for row in cursor.fetchall()]
                        self._log_transaction("query", query, params, len(results))
                        return results
                finally:
                    self._release_file_lock()
            else:
                # 其他级别：使用本地锁
                with self.get_connection() as conn:
                    cursor = conn.execute(query, params)
                    results = [dict(row) for row in cursor.fetchall()]
                    self._log_transaction("query", query, params, len(results))
                    return results
    
    def execute_update_with_optimistic_lock(self, query: str, params: tuple = (), 
                                          version_column: Optional[str] = None,
                                          version_value: Optional[int] = None) -> int:
        """
        执行更新语句（乐观锁控制）
        
        Args:
            query: SQL更新语句
            params: 更新参数
            version_column: 版本列名（用于乐观锁）
            version_value: 期望的版本值
            
        Returns:
            int: 受影响的行数
        """
        with self._write_lock:
            if not self._get_file_lock():
                raise Exception("无法获取数据库锁，操作失败")
            
            try:
                with self.get_connection() as conn:
                    # 如果使用乐观锁，先检查版本
                    if version_column and version_value is not None:
                        # 提取表名（简化实现）
                        table_name = self._extract_table_name(query)
                        if table_name:
                            check_query = f"SELECT {version_column} FROM {table_name} WHERE id = ?"
                            cursor = conn.execute(check_query, (params[0],))
                            current_version = cursor.fetchone()
                            if current_version and current_version[0] != version_value:
                                raise Exception(f"版本冲突：期望版本 {version_value}，实际版本 {current_version[0]}")
                    
                    cursor = conn.execute(query, params)
                    affected_rows = cursor.rowcount
                    conn.commit()
                    
                    self._log_transaction("update", query, params, affected_rows)
                    return affected_rows
            finally:
                self._release_file_lock()
    
    def execute_transaction_with_isolation(self, operations: List[tuple], 
                                         isolation_level: str = "serializable") -> bool:
        """
        执行事务（支持隔离级别）
        
        Args:
            operations: 操作列表，每个元素为 (query, params) 元组
            isolation_level: 隔离级别 ("read_uncommitted", "read_committed", "serializable")
            
        Returns:
            bool: 事务是否成功
        """
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
                        
                        # 记录事务日志
                        self._log_transaction("transaction", str(operations), (), True)
                        return True
                    except Exception as e:
                        logger.error(f"事务执行失败: {e}")
                        conn.rollback()
                        self._log_transaction("transaction", str(operations), (), False)
                        return False
            finally:
                self._release_file_lock()
    
    def _extract_table_name(self, query: str) -> Optional[str]:
        """从SQL查询中提取表名（简化实现）"""
        query_lower = query.lower().strip()
        if query_lower.startswith("update "):
            parts = query_lower.split()
            if len(parts) >= 2:
                return parts[1]
        elif query_lower.startswith("insert into "):
            parts = query_lower.split()
            if len(parts) >= 3:
                return parts[2]
        elif query_lower.startswith("delete from "):
            parts = query_lower.split()
            if len(parts) >= 3:
                return parts[2]
        return None
    
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
    
    def cleanup_old_transactions(self, max_age_hours: int = 24) -> int:
        """清理旧的事务日志"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            with open(self._transaction_log_path, 'r') as f:
                data = json.load(f)
            
            original_count = len(data.get("transactions", []))
            data["transactions"] = [
                tx for tx in data.get("transactions", [])
                if tx.get("timestamp", 0) > cutoff_time
            ]
            
            with open(self._transaction_log_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            cleaned_count = original_count - len(data["transactions"])
            logger.info(f"清理了 {cleaned_count} 条旧事务记录")
            return cleaned_count
        except Exception as e:
            logger.error(f"清理事务日志失败: {e}")
            return 0
    
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
    
    def close(self) -> None:
        """关闭数据库管理器"""
        try:
            self._release_file_lock()
            logger.info(f"Agent {self.agent_id} 数据库管理器已关闭")
        except Exception as e:
            logger.error(f"关闭数据库管理器失败: {e}")


class ConsistencyManager:
    """一致性管理器 - 处理多Agent数据一致性"""
    
    def __init__(self, db_manager: MultiAgentDatabaseManager):
        self.db_manager = db_manager
        self._consistency_cache = {}
        self._cache_lock = threading.Lock()
    
    def read_with_cache_validation(self, query: str, params: tuple = (), 
                                 cache_key: Optional[str] = None) -> List[Dict]:
        """
        带缓存验证的读取操作
        
        Args:
            query: SQL查询语句
            params: 查询参数
            cache_key: 缓存键（可选）
            
        Returns:
            list: 查询结果列表
        """
        if cache_key:
            with self._cache_lock:
                if cache_key in self._consistency_cache:
                    cached_result = self._consistency_cache[cache_key]
                    # 验证缓存是否仍然有效
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
    
    def _validate_cache(self, cache_key: str, cached_result: Dict) -> bool:
        """验证缓存是否有效"""
        # 简单的基于时间的缓存验证
        cache_age = time.time() - cached_result.get("timestamp", 0)
        return cache_age < 60  # 1分钟缓存有效期
    
    def update_with_version_check(self, query: str, params: tuple, 
                                table_name: str, record_id: int) -> bool:
        """
        带版本检查的更新操作
        
        Args:
            query: SQL更新语句
            params: 更新参数
            table_name: 表名
            record_id: 记录ID
            
        Returns:
            bool: 更新是否成功
        """
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
            
            # 清除相关缓存
            self._clear_related_cache(table_name, record_id)
            
            return affected_rows > 0
        except Exception as e:
            logger.error(f"版本检查更新失败: {e}")
            return False
    
    def _clear_related_cache(self, table_name: str, record_id: int) -> None:
        """清除相关缓存"""
        with self._cache_lock:
            keys_to_remove = [
                key for key in self._consistency_cache.keys()
                if table_name in key or str(record_id) in key
            ]
            for key in keys_to_remove:
                del self._consistency_cache[key]


# 全局实例
multi_agent_db_manager = MultiAgentDatabaseManager()
consistency_manager = ConsistencyManager(multi_agent_db_manager) 