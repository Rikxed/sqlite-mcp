"""
MCP网络服务器 - 支持HTTP连接
解决Docker容器中stdio连接超时问题
"""
import asyncio
import json
import logging
import sys
import uuid
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from database.connection import db_manager, thread_safe_db_manager
from config.settings import settings

logger = logging.getLogger(__name__)


class MCPRequest(BaseModel):
    """MCP请求模型"""
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPNetworkServer:
    """MCP网络服务器 - 支持HTTP连接"""
    
    def __init__(self, agent_id: Optional[str] = None, use_thread_safe: bool = False):
        """初始化MCP网络服务器"""
        self.agent_id = agent_id or str(uuid.uuid4())
        self.use_thread_safe = use_thread_safe
        self.db_manager = thread_safe_db_manager if use_thread_safe else db_manager
        
        # 标准MCP协议属性
        self.server_name = "sqlite-mcp-server"
        self.server_version = "1.0.0"
        self.protocol_version = "2024-11-05"
        self.initialized = False
        
        # 定义工具
        self.tools = self._define_tools()
        
        # FastAPI应用
        self.app = FastAPI(title="SQLite MCP Server", version="1.0.0")
        self._setup_routes()
        
        logger.info(f"MCP网络服务器初始化完成 - Agent ID: {self.agent_id}")
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """定义可用工具"""
        return [
            {
                "name": "sql_query",
                "description": "执行SQL查询语句，返回查询结果。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL查询语句"},
                        "params": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "sql_update",
                "description": "执行SQL更新语句，包括INSERT、UPDATE、DELETE操作。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL更新语句"},
                        "params": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_tables",
                "description": "列出数据库中的所有表。",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "describe_table",
                "description": "描述指定表的结构。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "表名"}
                    },
                    "required": ["table_name"]
                }
            }
        ]
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/")
        async def root():
            """根路径"""
            return {
                "name": self.server_name,
                "version": self.server_version,
                "protocol": self.protocol_version,
                "status": "running"
            }
        
        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            try:
                self.db_manager.execute_query("SELECT 1")
                return {"status": "healthy", "database": "connected"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        @self.app.post("/mcp")
        async def handle_mcp_request(request: MCPRequest):
            """处理MCP请求"""
            try:
                response = await self._handle_request(request.dict())
                return JSONResponse(content=response)
            except Exception as e:
                logger.error(f"处理MCP请求失败: {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "jsonrpc": "2.0",
                        "id": request.id,
                        "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                    }
                )
    
    async def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求"""
        try:
            method = request.get("method")
            
            if method != "initialize" and not self.initialized:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32002, "message": "Server not initialized"}
                }
            
            if method == "initialize":
                return await self._initialize(request)
            elif method == "tools/list":
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
    
    async def _initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """初始化连接"""
        params = request.get("params", {})
        client_info = params.get("clientInfo", {})
        
        logger.info(f"客户端初始化: {client_info.get('name', 'unknown')} v{client_info.get('version', 'unknown')}")
        
        self.initialized = True
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "protocolVersion": self.protocol_version,
                "capabilities": {
                    "tools": {},
                    "notifications": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": self.server_name,
                    "version": self.server_version
                }
            }
        }
    
    async def _list_tools(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """列出工具（字典风格）"""
        tools_dict = {}
        for tool in self.tools:
            tool_copy = tool.copy()
            name = tool_copy.pop("name")
            tools_dict[name] = tool_copy
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"tools": tools_dict}
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
        
        results = self.db_manager.execute_query(query, params)
        return f"查询成功，返回 {len(results)} 行结果:\n{json.dumps(results, ensure_ascii=False, indent=2)}"
    
    async def _execute_update(self, arguments: Dict[str, Any]) -> str:
        """执行更新"""
        query = arguments.get("query", "")
        params = tuple(arguments.get("params", []))
        
        affected_rows = self.db_manager.execute_update(query, params)
        return f"更新成功，影响 {affected_rows} 行"
    
    async def _list_tables(self, arguments: Dict[str, Any]) -> str:
        """列出所有表"""
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        results = self.db_manager.execute_query(query)
        table_names = [row['name'] for row in results]
        return f"数据库中的表:\n{json.dumps(table_names, ensure_ascii=False, indent=2)}"
    
    async def _describe_table(self, arguments: Dict[str, Any]) -> str:
        """描述表结构"""
        table_name = arguments.get("table_name", "")
        
        schema_query = f"PRAGMA table_info({table_name})"
        schema_results = self.db_manager.execute_query(schema_query)
        
        description = {
            "table_name": table_name,
            "columns": schema_results
        }
        
        return f"表 '{table_name}' 的结构:\n{json.dumps(description, ensure_ascii=False, indent=2)}"
    
    async def run(self, host: str = "0.0.0.0", port: int = 8000):
        """运行服务器"""
        logger.info(f"启动MCP网络服务器 - {host}:{port}")
        logger.info(f"HTTP端点: http://{host}:{port}")
        logger.info(f"健康检查: http://{host}:{port}/health")
        
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        server = uvicorn.Server(config)
        await server.serve()


def create_network_server(agent_id: Optional[str] = None, use_thread_safe: bool = False) -> MCPNetworkServer:
    """创建MCP网络服务器实例"""
    return MCPNetworkServer(agent_id, use_thread_safe) 