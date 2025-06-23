"""
标准MCP服务器实现
支持完整的MCP协议 (2024-11-05)
"""
import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional
from database.connection import db_manager
from config.settings import settings

logger = logging.getLogger(__name__)


class StandardMCPServer:
    """标准MCP服务器 - 支持完整MCP协议"""
    
    def __init__(self):
        """初始化服务器"""
        self.server_name = "sqlite-mcp-server"
        self.server_version = "1.0.0"
        self.protocol_version = "2024-11-05"
        self.initialized = False
        self.tools = self._define_tools()
        self.notifications = self._define_notifications()
        self.resources = self._define_resources()
    
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
                "name": "book_table",
                "description": "预订餐桌，减少指定时段的可用数量。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "restaurant_name": {"type": "string", "description": "餐厅名称"},
                        "capacity": {"type": "integer", "description": "桌型容量"},
                        "slot_start": {"type": "string", "description": "开始时间"},
                        "quantity": {"type": "integer", "description": "预订数量", "default": 1}
                    },
                    "required": ["restaurant_name", "capacity", "slot_start"]
                }
            }
        ]
    
    def _define_notifications(self) -> List[Dict[str, Any]]:
        """定义通知"""
        return [
            {
                "name": "database_changed",
                "description": "数据库发生变化时的通知"
            },
            {
                "name": "booking_created",
                "description": "预订创建成功的通知"
            }
        ]
    
    def _define_resources(self) -> List[Dict[str, Any]]:
        """定义资源"""
        return [
            {
                "uri": "sqlite:///restaurants",
                "name": "restaurants",
                "description": "餐厅信息",
                "mimeType": "application/json"
            },
            {
                "uri": "sqlite:///time_slots",
                "name": "time_slots",
                "description": "时段库存信息",
                "mimeType": "application/json"
            }
        ]
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求"""
        try:
            method = request.get("method")
            
            # 检查初始化状态
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
            elif method == "notifications/list":
                return await self._list_notifications(request)
            elif method == "resources/list":
                return await self._list_resources(request)
            elif method == "resources/read":
                return await self._read_resource(request)
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
            elif tool_name == "book_table":
                result = await self._book_table(arguments)
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
    
    async def _list_notifications(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """列出通知"""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"notifications": self.notifications}
        }
    
    async def _list_resources(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """列出资源"""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"resources": self.resources}
        }
    
    async def _read_resource(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """读取资源"""
        params = request.get("params", {})
        uri = params.get("uri")
        
        try:
            if uri == "sqlite:///restaurants":
                content = await self._get_restaurants_data()
            elif uri == "sqlite:///time_slots":
                content = await self._get_time_slots_data()
            else:
                raise ValueError(f"未知资源: {uri}")
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(content, ensure_ascii=False, indent=2)
                    }]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": f"读取资源失败: {str(e)}"}
            }
    
    # 工具实现方法
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
    
    async def _book_table(self, arguments: Dict[str, Any]) -> str:
        """预订餐桌"""
        restaurant_name = arguments.get("restaurant_name", "")
        capacity = arguments.get("capacity", 0)
        slot_start = arguments.get("slot_start", "")
        quantity = arguments.get("quantity", 1)
        
        # 检查可用性
        availability_query = """
            SELECT ts.available, ts.id
            FROM time_slots ts
            JOIN restaurants r ON ts.restaurant_id = r.id
            JOIN table_types tt ON ts.table_type_id = tt.id
            WHERE r.name = ? AND tt.capacity = ? AND ts.slot_start = ? AND ts.available >= ?
        """
        results = db_manager.execute_query(availability_query, (restaurant_name, capacity, slot_start, quantity))
        
        if not results:
            return f"错误: 找不到符合条件的可用时段"
        
        # 执行预订
        update_query = "UPDATE time_slots SET available = available - ? WHERE id = ?"
        affected_rows = db_manager.execute_update(update_query, (quantity, results[0]['id']))
        
        if affected_rows > 0:
            return f"预订成功！餐厅: {restaurant_name}, 桌型: {capacity}人桌, 时间: {slot_start}, 数量: {quantity}"
        else:
            return f"预订失败，请重试"
    
    # 资源数据方法
    async def _get_restaurants_data(self) -> List[Dict[str, Any]]:
        """获取餐厅数据"""
        query = "SELECT * FROM restaurants ORDER BY id"
        return db_manager.execute_query(query)
    
    async def _get_time_slots_data(self) -> List[Dict[str, Any]]:
        """获取时段库存数据"""
        query = """
            SELECT ts.*, r.name as restaurant_name, tt.capacity
            FROM time_slots ts
            JOIN restaurants r ON ts.restaurant_id = r.id
            JOIN table_types tt ON ts.table_type_id = tt.id
            WHERE ts.slot_start >= datetime('now')
            ORDER BY ts.slot_start
            LIMIT 20
        """
        return db_manager.execute_query(query)
    
    async def run(self):
        """运行服务器 - 标准stdio模式"""
        logger.info("启动标准MCP服务器 (stdio模式)...")
        
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


def create_standard_server() -> StandardMCPServer:
    """创建标准MCP服务器实例"""
    return StandardMCPServer() 