"""
MCP服务器核心实现
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from mcp import Server, StdioServerParameters
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

from database.connection import db_manager
from config.settings import settings

logger = logging.getLogger(__name__)


class SQLiteMCPServer:
    """SQLite MCP服务器"""
    
    def __init__(self):
        """初始化MCP服务器"""
        self.server = Server("sqlite-mcp-server")
        self._register_tools()
    
    def _register_tools(self) -> None:
        """注册所有工具"""
        self.server.list_tools(self._list_tools)
        self.server.call_tool(self._call_tool)
    
    async def _list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """列出可用工具"""
        tools = [
            Tool(
                name="execute_query",
                description="执行SQL查询语句，返回查询结果",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL查询语句"
                        },
                        "params": {
                            "type": "array",
                            "description": "查询参数列表",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="execute_update",
                description="执行SQL更新语句（INSERT、UPDATE、DELETE）",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL更新语句"
                        },
                        "params": {
                            "type": "array",
                            "description": "更新参数列表",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="list_tables",
                description="列出数据库中的所有表",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="describe_table",
                description="描述指定表的结构",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "表名"
                        }
                    },
                    "required": ["table_name"]
                }
            ),
            Tool(
                name="create_table",
                description="创建新表",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "表名"
                        },
                        "columns": {
                            "type": "string",
                            "description": "列定义SQL语句"
                        }
                    },
                    "required": ["table_name", "columns"]
                }
            )
        ]
        return ListToolsResult(tools=tools)
    
    async def _call_tool(self, request: CallToolRequest) -> CallToolResult:
        """调用工具"""
        try:
            if request.name == "execute_query":
                return await self._execute_query(request.arguments)
            elif request.name == "execute_update":
                return await self._execute_update(request.arguments)
            elif request.name == "list_tables":
                return await self._list_tables(request.arguments)
            elif request.name == "describe_table":
                return await self._describe_table(request.arguments)
            elif request.name == "create_table":
                return await self._create_table(request.arguments)
            else:
                raise ValueError(f"未知工具: {request.name}")
        except Exception as e:
            logger.error(f"工具调用失败: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"错误: {str(e)}"
                    )
                ],
                isError=True
            )
    
    async def _execute_query(self, arguments: Dict[str, Any]) -> CallToolResult:
        """执行查询"""
        query = arguments.get("query", "")
        params = tuple(arguments.get("params", []))
        
        try:
            results = db_manager.execute_query(query, params)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"查询成功，返回 {len(results)} 行结果:\n{json.dumps(results, ensure_ascii=False, indent=2)}"
                    )
                ]
            )
        except Exception as e:
            raise Exception(f"查询执行失败: {e}")
    
    async def _execute_update(self, arguments: Dict[str, Any]) -> CallToolResult:
        """执行更新"""
        query = arguments.get("query", "")
        params = tuple(arguments.get("params", []))
        
        try:
            affected_rows = db_manager.execute_update(query, params)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"更新成功，影响 {affected_rows} 行"
                    )
                ]
            )
        except Exception as e:
            raise Exception(f"更新执行失败: {e}")
    
    async def _list_tables(self, arguments: Dict[str, Any]) -> CallToolResult:
        """列出所有表"""
        try:
            query = """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """
            results = db_manager.execute_query(query)
            table_names = [row['name'] for row in results]
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"数据库中的表:\n{json.dumps(table_names, ensure_ascii=False, indent=2)}"
                    )
                ]
            )
        except Exception as e:
            raise Exception(f"获取表列表失败: {e}")
    
    async def _describe_table(self, arguments: Dict[str, Any]) -> CallToolResult:
        """描述表结构"""
        table_name = arguments.get("table_name", "")
        
        try:
            # 获取表结构
            schema_query = f"PRAGMA table_info({table_name})"
            schema_results = db_manager.execute_query(schema_query)
            
            # 获取表信息
            info_query = f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?"
            info_results = db_manager.execute_query(info_query, (table_name,))
            
            description = {
                "table_name": table_name,
                "columns": schema_results,
                "create_statement": info_results[0]['sql'] if info_results else None
            }
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"表 '{table_name}' 的结构:\n{json.dumps(description, ensure_ascii=False, indent=2)}"
                    )
                ]
            )
        except Exception as e:
            raise Exception(f"获取表结构失败: {e}")
    
    async def _create_table(self, arguments: Dict[str, Any]) -> CallToolResult:
        """创建表"""
        table_name = arguments.get("table_name", "")
        columns = arguments.get("columns", "")
        
        try:
            create_query = f"CREATE TABLE {table_name} ({columns})"
            db_manager.execute_update(create_query)
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"表 '{table_name}' 创建成功"
                    )
                ]
            )
        except Exception as e:
            raise Exception(f"创建表失败: {e}")
    
    async def run(self) -> None:
        """运行MCP服务器"""
        async with self.server.run_stdio(StdioServerParameters()) as stream:
            await stream.read_loop()


def create_server() -> SQLiteMCPServer:
    """创建MCP服务器实例"""
    return SQLiteMCPServer() 