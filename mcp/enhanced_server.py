"""
增强版MCP服务器 - 支持多Agent并发控制
"""
import asyncio
import json
import logging
import sys
import uuid
import time
from typing import Any, Dict, List, Optional
from database.connection import db_manager, thread_safe_db_manager
from config.settings import settings

logger = logging.getLogger(__name__)


class EnhancedMCPServer:
    """增强版MCP服务器 - 支持多Agent并发控制"""
    
    def __init__(self, agent_id: Optional[str] = None, use_thread_safe: bool = False):
        """
        初始化增强版MCP服务器
        
        Args:
            agent_id: Agent唯一标识符，如果为None则自动生成
            use_thread_safe: 是否使用线程安全的数据库管理器
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.use_thread_safe = use_thread_safe
        self.db_manager = thread_safe_db_manager if use_thread_safe else db_manager
        self.tools = self._define_tools()
        logger.info(f"增强版MCP服务器初始化完成 - Agent ID: {self.agent_id}")
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """定义可用工具"""
        return [
            {
                "name": "sql_query",
                "description": "执行SQL查询语句，返回查询结果。支持SELECT语句，可以查询数据、统计信息等。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL查询语句，如：SELECT * FROM users WHERE age > 18"},
                        "params": {"type": "array", "items": {"type": "string"}, "description": "查询参数列表"},
                        "consistency_level": {
                            "type": "string", 
                            "description": "一致性级别 (read_uncommitted, read_committed, serializable)",
                            "default": "read_committed"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "sql_update",
                "description": "执行SQL更新语句，包括INSERT、UPDATE、DELETE操作。用于添加、修改、删除数据。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL更新语句，如：INSERT INTO users (name, age) VALUES (?, ?)"},
                        "params": {"type": "array", "items": {"type": "string"}, "description": "更新参数列表"},
                        "use_optimistic_lock": {
                            "type": "boolean", 
                            "description": "是否使用乐观锁",
                            "default": False
                        },
                        "version_column": {
                            "type": "string", 
                            "description": "版本列名（乐观锁使用）"
                        },
                        "version_value": {
                            "type": "integer", 
                            "description": "期望的版本值（乐观锁使用）"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "sql_transaction",
                "description": "执行事务操作，支持多个SQL语句的原子性执行。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operations": {
                            "type": "array", 
                            "items": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string"},
                                    "params": {"type": "array", "items": {"type": "string"}}
                                },
                                "required": ["query"]
                            },
                            "description": "操作列表"
                        },
                        "isolation_level": {
                            "type": "string", 
                            "description": "隔离级别 (read_uncommitted, read_committed, serializable)",
                            "default": "serializable"
                        }
                    },
                    "required": ["operations"]
                }
            },
            {
                "name": "list_tables",
                "description": "列出数据库中的所有表。用于了解数据库结构。",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "consistency_level": {
                            "type": "string", 
                            "description": "一致性级别",
                            "default": "read_committed"
                        }
                    }
                }
            },
            {
                "name": "describe_table",
                "description": "描述指定表的结构，包括列名、数据类型、约束等信息。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "表名"},
                        "consistency_level": {
                            "type": "string", 
                            "description": "一致性级别",
                            "default": "read_committed"
                        }
                    },
                    "required": ["table_name"]
                }
            },
            {
                "name": "create_table",
                "description": "创建新表。可以定义表结构、列类型、约束等。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "表名"},
                        "columns": {"type": "string", "description": "列定义SQL语句，如：id INTEGER PRIMARY KEY, name TEXT NOT NULL"}
                    },
                    "required": ["table_name", "columns"]
                }
            },
            {
                "name": "database_info",
                "description": "获取数据库基本信息，包括表数量、数据库大小等统计信息。",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "consistency_level": {
                            "type": "string", 
                            "description": "一致性级别",
                            "default": "read_committed"
                        }
                    }
                }
            },
            {
                "name": "agent_status",
                "description": "获取当前Agent的状态信息，包括Agent ID、会话ID等。",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "transaction_history",
                "description": "获取事务历史记录，用于调试和监控。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer", 
                            "description": "返回的记录数量限制",
                            "default": 100
                        }
                    }
                }
            }
        ]
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求"""
        try:
            method = request.get("method")
            
            if method == "tools/list":
                return await self._list_tools(request)
            elif method == "tools/call":
                return await self._call_tool(request)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }
    
    async def _list_tools(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """列出工具"""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"tools": self.tools}
        }
    
    async def _call_tool(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "sql_query":
                result = await self._execute_query(arguments)
            elif tool_name == "sql_update":
                result = await self._execute_update(arguments)
            elif tool_name == "sql_transaction":
                result = await self._execute_transaction(arguments)
            elif tool_name == "list_tables":
                result = await self._list_tables(arguments)
            elif tool_name == "describe_table":
                result = await self._describe_table(arguments)
            elif tool_name == "create_table":
                result = await self._create_table(arguments)
            elif tool_name == "database_info":
                result = await self._database_info(arguments)
            elif tool_name == "agent_status":
                result = await self._agent_status(arguments)
            elif tool_name == "transaction_history":
                result = await self._transaction_history(arguments)
            else:
                raise ValueError(f"未知工具: {tool_name}")
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {"content": [{"type": "text", "text": result}]}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [{"type": "text", "text": f"错误: {str(e)}"}],
                    "isError": True
                }
            }
    
    async def _execute_query(self, arguments: Dict[str, Any]) -> str:
        """执行查询"""
        query = arguments.get("query", "")
        params = tuple(arguments.get("params", []))
        consistency_level = arguments.get("consistency_level", "read_committed")
        
        if self.use_thread_safe and hasattr(self.db_manager, 'execute_query_with_consistency'):
            results = self.db_manager.execute_query_with_consistency(query, params, consistency_level)
        else:
            results = self.db_manager.execute_query(query, params)
        
        return f"查询成功，返回 {len(results)} 行结果:\n{json.dumps(results, ensure_ascii=False, indent=2)}"
    
    async def _execute_update(self, arguments: Dict[str, Any]) -> str:
        """执行更新"""
        query = arguments.get("query", "")
        params = tuple(arguments.get("params", []))
        use_optimistic_lock = arguments.get("use_optimistic_lock", False)
        version_column = arguments.get("version_column")
        version_value = arguments.get("version_value")
        
        if self.use_thread_safe and hasattr(self.db_manager, 'execute_update_with_optimistic_lock'):
            if use_optimistic_lock and version_column and version_value is not None:
                affected_rows = self.db_manager.execute_update_with_optimistic_lock(
                    query, params, version_column, version_value
                )
            else:
                affected_rows = self.db_manager.execute_update(query, params)
        else:
            affected_rows = self.db_manager.execute_update(query, params)
        
        return f"更新成功，影响 {affected_rows} 行"
    
    async def _execute_transaction(self, arguments: Dict[str, Any]) -> str:
        """执行事务"""
        operations = arguments.get("operations", [])
        isolation_level = arguments.get("isolation_level", "serializable")
        
        # 转换操作格式
        formatted_operations = []
        for op in operations:
            query = op.get("query", "")
            params = tuple(op.get("params", []))
            formatted_operations.append((query, params))
        
        if self.use_thread_safe and hasattr(self.db_manager, 'execute_transaction_with_isolation'):
            success = self.db_manager.execute_transaction_with_isolation(formatted_operations, isolation_level)
        else:
            # 回退到普通事务
            success = self.db_manager.execute_transaction(formatted_operations)
        
        return f"事务执行{'成功' if success else '失败'}"
    
    async def _list_tables(self, arguments: Dict[str, Any]) -> str:
        """列出所有表"""
        consistency_level = arguments.get("consistency_level", "read_committed")
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        
        if self.use_thread_safe and hasattr(self.db_manager, 'execute_query_with_consistency'):
            results = self.db_manager.execute_query_with_consistency(query, (), consistency_level)
        else:
            results = self.db_manager.execute_query(query)
        
        table_names = [row['name'] for row in results]
        return f"数据库中的表:\n{json.dumps(table_names, ensure_ascii=False, indent=2)}"
    
    async def _describe_table(self, arguments: Dict[str, Any]) -> str:
        """描述表结构"""
        table_name = arguments.get("table_name", "")
        consistency_level = arguments.get("consistency_level", "read_committed")
        
        schema_query = f"PRAGMA table_info({table_name})"
        info_query = f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?"
        
        if self.use_thread_safe and hasattr(self.db_manager, 'execute_query_with_consistency'):
            schema_results = self.db_manager.execute_query_with_consistency(schema_query, (), consistency_level)
            info_results = self.db_manager.execute_query_with_consistency(info_query, (table_name,), consistency_level)
        else:
            schema_results = self.db_manager.execute_query(schema_query)
            info_results = self.db_manager.execute_query(info_query, (table_name,))
        
        description = {
            "table_name": table_name,
            "columns": schema_results,
            "create_statement": info_results[0]['sql'] if info_results else None
        }
        
        return f"表 '{table_name}' 的结构:\n{json.dumps(description, ensure_ascii=False, indent=2)}"
    
    async def _create_table(self, arguments: Dict[str, Any]) -> str:
        """创建表"""
        table_name = arguments.get("table_name", "")
        columns = arguments.get("columns", "")
        
        create_query = f"CREATE TABLE {table_name} ({columns})"
        self.db_manager.execute_update(create_query)
        return f"表 '{table_name}' 创建成功"
    
    async def _database_info(self, arguments: Dict[str, Any]) -> str:
        """获取数据库信息"""
        consistency_level = arguments.get("consistency_level", "read_committed")
        
        tables_query = """
            SELECT COUNT(*) as table_count FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """
        size_query = "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
        tables_list_query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        
        if self.use_thread_safe and hasattr(self.db_manager, 'execute_query_with_consistency'):
            table_count = self.db_manager.execute_query_with_consistency(tables_query, (), consistency_level)[0]['table_count']
            size_result = self.db_manager.execute_query_with_consistency(size_query, (), consistency_level)
            tables = self.db_manager.execute_query_with_consistency(tables_list_query, (), consistency_level)
        else:
            table_count = self.db_manager.execute_query(tables_query)[0]['table_count']
            size_result = self.db_manager.execute_query(size_query)
            tables = self.db_manager.execute_query(tables_list_query)
        
        db_size = size_result[0]['size'] if size_result else 0
        table_names = [row['name'] for row in tables]
        
        info = {
            "database_path": settings.database_path,
            "agent_id": self.agent_id,
            "use_thread_safe": self.use_thread_safe,
            "table_count": table_count,
            "database_size_bytes": db_size,
            "tables": table_names
        }
        
        return f"数据库信息:\n{json.dumps(info, ensure_ascii=False, indent=2)}"
    
    async def _agent_status(self, arguments: Dict[str, Any]) -> str:
        """获取Agent状态"""
        if self.use_thread_safe and hasattr(self.db_manager, 'get_agent_status'):
            status = self.db_manager.get_agent_status()
        else:
            status = {
                "agent_id": self.agent_id,
                "use_thread_safe": self.use_thread_safe,
                "database_path": settings.database_path,
                "timestamp": time.time()
            }
        
        return f"Agent状态:\n{json.dumps(status, ensure_ascii=False, indent=2)}"
    
    async def _transaction_history(self, arguments: Dict[str, Any]) -> str:
        """获取事务历史"""
        limit = arguments.get("limit", 100)
        
        if self.use_thread_safe and hasattr(self.db_manager, 'get_transaction_history'):
            history = self.db_manager.get_transaction_history(limit)
        else:
            history = []
        
        return f"事务历史 (最近 {len(history)} 条):\n{json.dumps(history, ensure_ascii=False, indent=2)}"
    
    async def run(self):
        """运行服务器 - 标准stdio模式"""
        logger.info(f"启动增强版MCP服务器 (stdio模式) - Agent ID: {self.agent_id}")
        
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
                
            except KeyboardInterrupt:
                logger.info("服务器被用户中断")
                break
            except Exception as e:
                logger.error(f"处理请求时出错: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
                }
                print(json.dumps(error_response, ensure_ascii=False))
                sys.stdout.flush()


def create_enhanced_server(agent_id: Optional[str] = None, use_thread_safe: bool = False) -> EnhancedMCPServer:
    """创建增强版MCP服务器实例"""
    return EnhancedMCPServer(agent_id, use_thread_safe) 