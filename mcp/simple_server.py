"""
简化的MCP服务器实现 - 支持自然语言交互
"""
import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional
from database.connection import db_manager
from config.settings import settings

logger = logging.getLogger(__name__)


class SimpleMCPServer:
    """简化的MCP服务器 - 支持自然语言交互"""
    
    def __init__(self):
        """初始化服务器"""
        self.tools = self._define_tools()
    
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
                        "params": {"type": "array", "items": {"type": "string"}, "description": "查询参数列表"}
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
                        "params": {"type": "array", "items": {"type": "string"}, "description": "更新参数列表"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_tables",
                "description": "列出数据库中的所有表。用于了解数据库结构。",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "describe_table",
                "description": "描述指定表的结构，包括列名、数据类型、约束等信息。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "表名"}
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
                "inputSchema": {"type": "object", "properties": {}}
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
            elif tool_name == "list_tables":
                result = await self._list_tables(arguments)
            elif tool_name == "describe_table":
                result = await self._describe_table(arguments)
            elif tool_name == "create_table":
                result = await self._create_table(arguments)
            elif tool_name == "database_info":
                result = await self._database_info(arguments)
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
        
        results = db_manager.execute_query(query, params)
        return f"查询成功，返回 {len(results)} 行结果:\n{json.dumps(results, ensure_ascii=False, indent=2)}"
    
    async def _execute_update(self, arguments: Dict[str, Any]) -> str:
        """执行更新"""
        query = arguments.get("query", "")
        params = tuple(arguments.get("params", []))
        
        affected_rows = db_manager.execute_update(query, params)
        return f"更新成功，影响 {affected_rows} 行"
    
    async def _list_tables(self, arguments: Dict[str, Any]) -> str:
        """列出所有表"""
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        results = db_manager.execute_query(query)
        table_names = [row['name'] for row in results]
        return f"数据库中的表:\n{json.dumps(table_names, ensure_ascii=False, indent=2)}"
    
    async def _describe_table(self, arguments: Dict[str, Any]) -> str:
        """描述表结构"""
        table_name = arguments.get("table_name", "")
        
        schema_query = f"PRAGMA table_info({table_name})"
        schema_results = db_manager.execute_query(schema_query)
        
        info_query = f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?"
        info_results = db_manager.execute_query(info_query, (table_name,))
        
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
        db_manager.execute_update(create_query)
        return f"表 '{table_name}' 创建成功"
    
    async def _database_info(self, arguments: Dict[str, Any]) -> str:
        """获取数据库信息"""
        # 获取表数量
        tables_query = """
            SELECT COUNT(*) as table_count FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """
        table_count = db_manager.execute_query(tables_query)[0]['table_count']
        
        # 获取数据库大小
        size_query = "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
        size_result = db_manager.execute_query(size_query)
        db_size = size_result[0]['size'] if size_result else 0
        
        # 获取所有表名
        tables_query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        tables = db_manager.execute_query(tables_query)
        table_names = [row['name'] for row in tables]
        
        info = {
            "database_path": settings.database_path,
            "table_count": table_count,
            "database_size_bytes": db_size,
            "tables": table_names
        }
        
        return f"数据库信息:\n{json.dumps(info, ensure_ascii=False, indent=2)}"
    
    async def run(self):
        """运行服务器 - 标准stdio模式"""
        logger.info("启动简化MCP服务器 (stdio模式)...")
        
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


def create_simple_server() -> SimpleMCPServer:
    """创建简化MCP服务器实例"""
    return SimpleMCPServer() 