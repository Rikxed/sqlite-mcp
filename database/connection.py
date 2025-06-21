"""
SQLite数据库连接管理模块
"""
import sqlite3
import logging
import threading
from contextlib import contextmanager
from typing import Generator, Optional
from pathlib import Path
from queue import Queue, Empty
import time

from config.settings import settings

logger = logging.getLogger(__name__)


class ThreadSafeDatabaseManager:
    """线程安全的数据库管理器"""
    
    def __init__(self, db_path: Optional[str] = None, max_connections: int = 10):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，如果为None则使用配置中的路径
            max_connections: 最大连接数
        """
        self.db_path = db_path or settings.database_path
        self.max_connections = max_connections
        self._connection_pool = Queue(maxsize=max_connections)
        self._lock = threading.RLock()  # 可重入锁
        self._write_lock = threading.Lock()  # 写操作专用锁
        self._ensure_data_directory()
        self._init_database()
        self._run_init_script()
        self._init_connection_pool()
    
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
                conn.execute("PRAGMA busy_timeout = 30000")  # 30秒超时
                # 设置缓存大小
                conn.execute("PRAGMA cache_size = -64000")  # 64MB缓存
                logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _init_connection_pool(self) -> None:
        """初始化连接池"""
        for _ in range(self.max_connections):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                # 设置连接参数
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA busy_timeout = 30000")
                self._connection_pool.put(conn)
            except Exception as e:
                logger.error(f"创建连接池连接失败: {e}")
                raise
    
    def _get_connection_from_pool(self) -> sqlite3.Connection:
        """从连接池获取连接"""
        try:
            # 设置超时时间，避免无限等待
            conn = self._connection_pool.get(timeout=5)
            return conn
        except Empty:
            raise Exception("连接池已满，无法获取连接")
    
    def _return_connection_to_pool(self, conn: sqlite3.Connection) -> None:
        """将连接返回连接池"""
        try:
            # 重置连接状态
            conn.rollback()
            self._connection_pool.put(conn, timeout=1)
        except Exception as e:
            logger.error(f"返回连接到池失败: {e}")
            # 如果返回失败，关闭连接
            try:
                conn.close()
            except:
                pass
    
    def _run_init_script(self) -> None:
        """运行初始化脚本"""
        if not settings.init_script:
            logger.info("未配置初始化脚本，跳过初始化")
            return
        
        init_script_path = Path(settings.init_script)
        if not init_script_path.exists():
            logger.warning(f"初始化脚本不存在: {settings.init_script}")
            return
        
        try:
            logger.info(f"执行初始化脚本: {settings.init_script}")
            with open(init_script_path, 'r', encoding='utf-8') as f:
                init_sql = f.read()
            
            # 分割SQL语句并执行
            statements = [stmt.strip() for stmt in init_sql.split(';') if stmt.strip()]
            for stmt in statements:
                if stmt:
                    self.execute_update(stmt)
            
            logger.info("初始化脚本执行完成")
        except Exception as e:
            logger.error(f"初始化脚本执行失败: {e}")
            raise
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        获取数据库连接的上下文管理器（线程安全）
        
        Yields:
            sqlite3.Connection: 数据库连接对象
        """
        conn = None
        try:
            with self._lock:
                conn = self._get_connection_from_pool()
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
                self._return_connection_to_pool(conn)
    
    def execute_query(self, query: str, params: tuple = ()) -> list:
        """
        执行查询语句（线程安全）
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            list: 查询结果列表
        """
        with self._lock:  # 读操作使用可重入锁
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        执行更新语句（线程安全）
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            int: 受影响的行数
        """
        with self._write_lock:  # 写操作使用专用锁
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                conn.commit()
                return cursor.rowcount
    
    def execute_many(self, query: str, params_list: list) -> int:
        """
        批量执行SQL语句（线程安全）
        
        Args:
            query: SQL语句
            params_list: 参数列表
            
        Returns:
            int: 受影响的行数
        """
        with self._write_lock:  # 批量操作使用写锁
            with self.get_connection() as conn:
                cursor = conn.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
    
    def execute_transaction(self, operations: list) -> bool:
        """
        执行事务（线程安全）
        
        Args:
            operations: 操作列表，每个元素为 (query, params) 元组
            
        Returns:
            bool: 事务是否成功
        """
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
    
    def close(self) -> None:
        """关闭所有连接"""
        while not self._connection_pool.empty():
            try:
                conn = self._connection_pool.get_nowait()
                conn.close()
            except Empty:
                break


class DatabaseManager:
    """数据库管理器（向后兼容）"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，如果为None则使用配置中的路径
        """
        self.db_path = db_path or settings.database_path
        self._ensure_data_directory()
        self._init_database()
        self._run_init_script()
    
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
                logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _run_init_script(self) -> None:
        """运行初始化脚本"""
        if not settings.init_script:
            logger.info("未配置初始化脚本，跳过初始化")
            return
        
        init_script_path = Path(settings.init_script)
        if not init_script_path.exists():
            logger.warning(f"初始化脚本不存在: {settings.init_script}")
            return
        
        try:
            logger.info(f"执行初始化脚本: {settings.init_script}")
            with open(init_script_path, 'r', encoding='utf-8') as f:
                init_sql = f.read()
            
            # 分割SQL语句并执行
            statements = [stmt.strip() for stmt in init_sql.split(';') if stmt.strip()]
            for stmt in statements:
                if stmt:
                    self.execute_update(stmt)
            
            logger.info("初始化脚本执行完成")
        except Exception as e:
            logger.error(f"初始化脚本执行失败: {e}")
            raise
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        获取数据库连接的上下文管理器
        
        Yields:
            sqlite3.Connection: 数据库连接对象
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            yield conn
        except Exception as e:
            logger.error(f"数据库连接错误: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> list:
        """
        执行查询语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            list: 查询结果列表
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        执行更新语句
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            int: 受影响的行数
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_many(self, query: str, params_list: list) -> int:
        """
        批量执行SQL语句
        
        Args:
            query: SQL语句
            params_list: 参数列表
            
        Returns:
            int: 受影响的行数
        """
        with self.get_connection() as conn:
            cursor = conn.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount


# 全局数据库管理器实例
db_manager = DatabaseManager()

# 线程安全的数据库管理器实例（延迟初始化）
thread_safe_db_manager = None

def get_thread_safe_db_manager():
    """获取线程安全的数据库管理器实例（延迟初始化）"""
    global thread_safe_db_manager
    if thread_safe_db_manager is None:
        thread_safe_db_manager = ThreadSafeDatabaseManager()
    return thread_safe_db_manager 