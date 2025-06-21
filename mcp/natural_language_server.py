"""
自然语言MCP服务器 - 支持自然语言建表和查询
"""
import asyncio
import json
import logging
import sys
import re
from typing import Any, Dict, List, Optional
from database.connection import db_manager
from config.settings import settings

logger = logging.getLogger(__name__)


class NaturalLanguageMCPServer:
    """自然语言MCP服务器 - 支持自然语言建表和查询"""
    
    def __init__(self):
        """初始化服务器"""
        self.tools = self._define_tools()
        logger.info("自然语言MCP服务器初始化完成")
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """定义可用工具"""
        return [
            {
                "name": "natural_language_query",
                "description": "使用自然语言执行数据库查询。支持中文描述，自动转换为SQL查询。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string", 
                            "description": "自然语言查询描述，如：查询所有年龄大于18的用户"
                        }
                    },
                    "required": ["description"]
                }
            },
            {
                "name": "natural_language_create_table",
                "description": "使用自然语言创建数据库表。支持中文描述，自动生成表结构。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string", 
                            "description": "自然语言表结构描述，如：创建一个用户表，包含姓名、年龄、邮箱字段"
                        }
                    },
                    "required": ["description"]
                }
            },
            {
                "name": "natural_language_insert",
                "description": "使用自然语言插入数据。支持中文描述，自动转换为INSERT语句。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string", 
                            "description": "自然语言插入描述，如：向用户表插入一个叫张三的用户，年龄25岁"
                        }
                    },
                    "required": ["description"]
                }
            },
            {
                "name": "natural_language_update",
                "description": "使用自然语言更新数据。支持中文描述，自动转换为UPDATE语句。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string", 
                            "description": "自然语言更新描述，如：将用户张三的年龄改为26岁"
                        }
                    },
                    "required": ["description"]
                }
            },
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
    
    def _parse_create_table_description(self, description: str) -> Dict[str, Any]:
        """解析自然语言建表描述"""
        # 提取表名
        table_name_match = re.search(r'创建(一个)?(.+?)表', description)
        if not table_name_match:
            raise ValueError("无法识别表名，请使用'创建xxx表'的格式")
        
        table_name = table_name_match.group(2).strip()
        
        # 提取字段信息
        fields = []
        
        # 常见的字段类型映射
        field_type_mapping = {
            '姓名': 'TEXT',
            '名字': 'TEXT', 
            '名称': 'TEXT',
            '标题': 'TEXT',
            '描述': 'TEXT',
            '内容': 'TEXT',
            '地址': 'TEXT',
            '电话': 'TEXT',
            '手机': 'TEXT',
            '邮箱': 'TEXT',
            '邮件': 'TEXT',
            '年龄': 'INTEGER',
            '数量': 'INTEGER',
            '价格': 'REAL',
            '金额': 'REAL',
            '分数': 'REAL',
            '时间': 'TIMESTAMP',
            '日期': 'DATE',
            '创建时间': 'TIMESTAMP',
            '更新时间': 'TIMESTAMP'
        }
        
        # 提取字段
        field_patterns = [
            r'包含(.+?)字段',
            r'有(.+?)字段',
            r'包含(.+?)等字段',
            r'字段包括(.+?)',
            r'字段有(.+?)'
        ]
        
        field_text = ""
        for pattern in field_patterns:
            match = re.search(pattern, description)
            if match:
                field_text = match.group(1)
                break
        
        if not field_text:
            # 如果没有明确的字段描述，尝试从整个描述中提取
            field_text = description
        
        # 分割字段
        field_segments = re.split(r'[,，、和]', field_text)
        
        for segment in field_segments:
            segment = segment.strip()
            if not segment or segment in ['字段', '等']:
                continue
            
            # 确定字段类型
            field_type = 'TEXT'  # 默认类型
            for key, value in field_type_mapping.items():
                if key in segment:
                    field_type = value
                    break
            
            # 提取字段名
            field_name = segment.replace('字段', '').replace('等', '').strip()
            if field_name:
                fields.append({
                    'name': field_name,
                    'type': field_type
                })
        
        # 如果没有提取到字段，添加默认字段
        if not fields:
            fields = [
                {'name': 'id', 'type': 'INTEGER PRIMARY KEY'},
                {'name': 'name', 'type': 'TEXT'},
                {'name': 'created_at', 'type': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'}
            ]
        
        return {
            'table_name': table_name,
            'fields': fields
        }
    
    def _generate_create_table_sql(self, table_info: Dict[str, Any]) -> str:
        """生成建表SQL"""
        table_name = table_info['table_name']
        fields = table_info['fields']
        
        # 构建字段定义
        field_definitions = []
        for field in fields:
            field_name = field['name']
            field_type = field['type']
            
            # 处理主键
            if 'PRIMARY KEY' in field_type:
                field_definitions.append(f"{field_name} {field_type}")
            else:
                field_definitions.append(f"{field_name} {field_type}")
        
        columns = ', '.join(field_definitions)
        return f"CREATE TABLE {table_name} ({columns})"
    
    def _parse_query_description(self, description: str) -> str:
        """解析自然语言查询描述"""
        # 简单的查询模式匹配
        if '查询' in description or '查找' in description or '搜索' in description:
            # 提取表名
            table_match = re.search(r'(.+?)表', description)
            if table_match:
                table_name = table_match.group(1)
                
                # 构建基本查询
                query = f"SELECT * FROM {table_name}"
                
                # 添加条件
                if '年龄大于' in description:
                    age_match = re.search(r'年龄大于(\d+)', description)
                    if age_match:
                        age = age_match.group(1)
                        query += f" WHERE age > {age}"
                elif '年龄小于' in description:
                    age_match = re.search(r'年龄小于(\d+)', description)
                    if age_match:
                        age = age_match.group(1)
                        query += f" WHERE age < {age}"
                elif '姓名' in description or '名字' in description:
                    name_match = re.search(r'姓名[是为](.+)', description)
                    if name_match:
                        name = name_match.group(1)
                        query += f" WHERE name = '{name}'"
                
                return query
        
        # 如果没有匹配到模式，返回默认查询
        return "SELECT * FROM users LIMIT 10"
    
    def _parse_insert_description(self, description: str) -> Dict[str, Any]:
        """解析自然语言插入描述"""
        # 提取表名
        table_match = re.search(r'向(.+?)表', description)
        if not table_match:
            raise ValueError("无法识别表名，请使用'向xxx表插入'的格式")
        
        table_name = table_match.group(1)
        
        # 提取数据
        data = {}
        
        # 提取姓名
        name_match = re.search(r'叫(.+?)的', description)
        if name_match:
            data['name'] = name_match.group(1)
        
        # 提取年龄
        age_match = re.search(r'年龄(\d+)岁', description)
        if age_match:
            data['age'] = int(age_match.group(1))
        
        # 提取邮箱
        email_match = re.search(r'邮箱[是为](.+)', description)
        if email_match:
            data['email'] = email_match.group(1)
        
        return {
            'table_name': table_name,
            'data': data
        }
    
    def _generate_insert_sql(self, insert_info: Dict[str, Any]) -> str:
        """生成插入SQL"""
        table_name = insert_info['table_name']
        data = insert_info['data']
        
        if not data:
            raise ValueError("没有提取到有效的数据")
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = list(data.values())
        
        return f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values
    
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
            if tool_name == "natural_language_query":
                result = await self._execute_natural_language_query(arguments)
            elif tool_name == "natural_language_create_table":
                result = await self._execute_natural_language_create_table(arguments)
            elif tool_name == "natural_language_insert":
                result = await self._execute_natural_language_insert(arguments)
            elif tool_name == "natural_language_update":
                result = await self._execute_natural_language_update(arguments)
            elif tool_name == "sql_query":
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
    
    async def _execute_natural_language_query(self, arguments: Dict[str, Any]) -> str:
        """执行自然语言查询"""
        description = arguments.get("description", "")
        
        # 解析自然语言描述
        sql_query = self._parse_query_description(description)
        
        # 执行查询
        results = db_manager.execute_query(sql_query)
        
        return f"自然语言查询: {description}\n生成的SQL: {sql_query}\n查询结果:\n{json.dumps(results, ensure_ascii=False, indent=2)}"
    
    async def _execute_natural_language_create_table(self, arguments: Dict[str, Any]) -> str:
        """执行自然语言建表"""
        description = arguments.get("description", "")
        
        # 解析自然语言描述
        table_info = self._parse_create_table_description(description)
        
        # 生成SQL
        create_sql = self._generate_create_table_sql(table_info)
        
        # 执行建表
        db_manager.execute_update(create_sql)
        
        return f"自然语言建表: {description}\n生成的SQL: {create_sql}\n表结构:\n{json.dumps(table_info, ensure_ascii=False, indent=2)}"
    
    async def _execute_natural_language_insert(self, arguments: Dict[str, Any]) -> str:
        """执行自然语言插入"""
        description = arguments.get("description", "")
        
        # 解析自然语言描述
        insert_info = self._parse_insert_description(description)
        
        # 生成SQL
        sql_query, params = self._generate_insert_sql(insert_info)
        
        # 执行插入
        affected_rows = db_manager.execute_update(sql_query, tuple(params))
        
        return f"自然语言插入: {description}\n生成的SQL: {sql_query}\n参数: {params}\n影响行数: {affected_rows}"
    
    async def _execute_natural_language_update(self, arguments: Dict[str, Any]) -> str:
        """执行自然语言更新"""
        description = arguments.get("description", "")
        
        # 简单的更新模式匹配
        if '将' in description and '改为' in description:
            # 提取表名
            table_match = re.search(r'将(.+?)的', description)
            if table_match:
                table_name = "users"  # 默认表名
                
                # 提取字段和值
                field_value_match = re.search(r'(.+?)改为(.+)', description)
                if field_value_match:
                    field = field_value_match.group(1)
                    value = field_value_match.group(2)
                    
                    # 字段映射
                    field_mapping = {
                        '年龄': 'age',
                        '姓名': 'name',
                        '名字': 'name',
                        '邮箱': 'email'
                    }
                    
                    sql_field = field_mapping.get(field, field)
                    
                    # 构建SQL
                    sql_query = f"UPDATE {table_name} SET {sql_field} = ? WHERE name = ?"
                    params = [value, table_match.group(1)]
                    
                    # 执行更新
                    affected_rows = db_manager.execute_update(sql_query, tuple(params))
                    
                    return f"自然语言更新: {description}\n生成的SQL: {sql_query}\n参数: {params}\n影响行数: {affected_rows}"
        
        return f"无法解析更新描述: {description}"
    
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
        tables_query = """
            SELECT COUNT(*) as table_count FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """
        table_count = db_manager.execute_query(tables_query)[0]['table_count']
        
        size_query = "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
        size_result = db_manager.execute_query(size_query)
        db_size = size_result[0]['size'] if size_result else 0
        
        tables_list_query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        tables = db_manager.execute_query(tables_list_query)
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
        logger.info("启动自然语言MCP服务器 (stdio模式)...")
        
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


def create_natural_language_server() -> NaturalLanguageMCPServer:
    """创建自然语言MCP服务器实例"""
    return NaturalLanguageMCPServer() 