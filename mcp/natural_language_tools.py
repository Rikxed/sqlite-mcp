"""
自然语言数据库操作工具
提供自然语言到SQL的转换和数据库操作功能
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    """数据库适配器，用于统一不同数据库管理器的接口"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def execute_sql(self, sql: str, agent_id: str = "nl_agent") -> Any:
        """执行SQL语句的统一接口"""
        try:
            # 检查是否是MultiAgentDatabaseManager
            if hasattr(self.db_manager, 'execute_sql'):
                return self.db_manager.execute_sql(sql, agent_id)
            
            # 检查是否是普通数据库管理器
            elif hasattr(self.db_manager, 'execute_query') and hasattr(self.db_manager, 'execute_update'):
                # 判断是查询还是更新操作
                sql_upper = sql.strip().upper()
                if sql_upper.startswith('SELECT'):
                    return self.db_manager.execute_query(sql)
                else:
                    return self.db_manager.execute_update(sql)
            
            # 检查是否是线程安全的数据库管理器
            elif hasattr(self.db_manager, 'execute_query_with_consistency'):
                sql_upper = sql.strip().upper()
                if sql_upper.startswith('SELECT'):
                    return self.db_manager.execute_query_with_consistency(sql, (), "read_committed")
                else:
                    return self.db_manager.execute_update(sql)
            
            else:
                raise ValueError(f"不支持的数据库管理器类型: {type(self.db_manager)}")
                
        except Exception as e:
            logger.error(f"执行SQL时出错: {e}")
            raise e


class NaturalLanguageProcessor:
    """自然语言处理器"""
    
    def __init__(self, db_manager):
        self.db_adapter = DatabaseAdapter(db_manager)
        self.table_patterns = {
            'create': [
                r'创建表\s+(\w+)\s+包含\s+(.+)',
                r'建立表\s+(\w+)\s+字段\s+(.+)',
                r'新建表\s+(\w+)\s+列\s+(.+)',
                r'create\s+table\s+(\w+)\s+with\s+(.+)',
                r'create\s+table\s+(\w+)\s+columns\s+(.+)'
            ],
            'insert': [
                r'插入\s+(.+)\s+到\s+(\w+)',
                r'添加\s+(.+)\s+到\s+(\w+)',
                r'insert\s+(.+)\s+into\s+(\w+)',
                r'add\s+(.+)\s+to\s+(\w+)'
            ],
            'select': [
                r'查询\s+(.+)\s+从\s+(\w+)',
                r'查找\s+(.+)\s+在\s+(\w+)',
                r'select\s+(.+)\s+from\s+(\w+)',
                r'find\s+(.+)\s+in\s+(\w+)'
            ],
            'update': [
                r'更新\s+(\w+)\s+设置\s+(.+)\s+条件\s+(.+)',
                r'修改\s+(\w+)\s+设置\s+(.+)\s+当\s+(.+)',
                r'update\s+(\w+)\s+set\s+(.+)\s+where\s+(.+)',
                r'modify\s+(\w+)\s+set\s+(.+)\s+when\s+(.+)'
            ],
            'delete': [
                r'删除\s+(\w+)\s+条件\s+(.+)',
                r'删除\s+(\w+)\s+当\s+(.+)',
                r'delete\s+from\s+(\w+)\s+where\s+(.+)',
                r'remove\s+from\s+(\w+)\s+when\s+(.+)'
            ]
        }
        
        # 字段类型映射
        self.type_mapping = {
            '文本': 'TEXT',
            '字符串': 'TEXT',
            '数字': 'INTEGER',
            '整数': 'INTEGER',
            '小数': 'REAL',
            '浮点数': 'REAL',
            '日期': 'TEXT',
            '时间': 'TEXT',
            '布尔': 'INTEGER',
            'text': 'TEXT',
            'string': 'TEXT',
            'number': 'INTEGER',
            'integer': 'INTEGER',
            'decimal': 'REAL',
            'float': 'REAL',
            'date': 'TEXT',
            'time': 'TEXT',
            'boolean': 'INTEGER'
        }
    
    def process_natural_language(self, query: str, agent_id: str = "nl_agent") -> Dict[str, Any]:
        """
        处理自然语言查询
        
        Args:
            query: 自然语言查询
            agent_id: 代理ID
            
        Returns:
            处理结果字典
        """
        try:
            query = query.strip()
            
            # 检测操作类型
            operation = self._detect_operation(query)
            
            if operation == 'create':
                return self._handle_create_table(query, agent_id)
            elif operation == 'insert':
                return self._handle_insert(query, agent_id)
            elif operation == 'select':
                return self._handle_select(query, agent_id)
            elif operation == 'update':
                return self._handle_update(query, agent_id)
            elif operation == 'delete':
                return self._handle_delete(query, agent_id)
            else:
                return {
                    'success': False,
                    'error': f'无法识别的操作类型: {query}',
                    'suggestion': '请使用以下格式之一:\n- 创建表 表名 包含 字段1:类型,字段2:类型\n- 插入 数据 到 表名\n- 查询 字段 从 表名\n- 更新 表名 设置 字段=值 条件 条件\n- 删除 表名 条件 条件'
                }
                
        except Exception as e:
            logger.error(f"处理自然语言查询时出错: {e}")
            return {
                'success': False,
                'error': f'处理查询时出错: {str(e)}'
            }
    
    def _detect_operation(self, query: str) -> Optional[str]:
        """检测操作类型"""
        query_lower = query.lower()
        
        if any(re.search(pattern, query_lower) for pattern in self.table_patterns['create']):
            return 'create'
        elif any(re.search(pattern, query_lower) for pattern in self.table_patterns['insert']):
            return 'insert'
        elif any(re.search(pattern, query_lower) for pattern in self.table_patterns['select']):
            return 'select'
        elif any(re.search(pattern, query_lower) for pattern in self.table_patterns['update']):
            return 'update'
        elif any(re.search(pattern, query_lower) for pattern in self.table_patterns['delete']):
            return 'delete'
        
        return None
    
    def _handle_create_table(self, query: str, agent_id: str) -> Dict[str, Any]:
        """处理创建表操作"""
        for pattern in self.table_patterns['create']:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                table_name = match.group(1)
                fields_desc = match.group(2)
                
                # 解析字段定义
                fields = self._parse_fields(fields_desc)
                if not fields:
                    return {
                        'success': False,
                        'error': f'无法解析字段定义: {fields_desc}'
                    }
                
                # 生成SQL
                sql = self._generate_create_sql(table_name, fields)
                
                # 执行SQL
                result = self.db_adapter.execute_sql(sql, agent_id)
                
                return {
                    'success': True,
                    'operation': 'create_table',
                    'table_name': table_name,
                    'sql': sql,
                    'result': result,
                    'message': f'成功创建表 {table_name}，包含 {len(fields)} 个字段'
                }
        
        return {
            'success': False,
            'error': f'无法解析创建表命令: {query}'
        }
    
    def _handle_insert(self, query: str, agent_id: str) -> Dict[str, Any]:
        """处理插入操作"""
        for pattern in self.table_patterns['insert']:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                data_desc = match.group(1)
                table_name = match.group(2)
                
                # 解析数据
                data = self._parse_insert_data(data_desc)
                if not data:
                    return {
                        'success': False,
                        'error': f'无法解析插入数据: {data_desc}'
                    }
                
                # 生成SQL
                sql = self._generate_insert_sql(table_name, data)
                
                # 执行SQL
                result = self.db_adapter.execute_sql(sql, agent_id)
                
                return {
                    'success': True,
                    'operation': 'insert',
                    'table_name': table_name,
                    'sql': sql,
                    'result': result,
                    'message': f'成功向表 {table_name} 插入数据'
                }
        
        return {
            'success': False,
            'error': f'无法解析插入命令: {query}'
        }
    
    def _handle_select(self, query: str, agent_id: str) -> Dict[str, Any]:
        """处理查询操作"""
        for pattern in self.table_patterns['select']:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                fields_desc = match.group(1)
                table_name = match.group(2)
                
                # 解析字段
                fields = self._parse_select_fields(fields_desc)
                
                # 生成SQL
                sql = self._generate_select_sql(table_name, fields)
                
                # 执行SQL
                result = self.db_adapter.execute_sql(sql, agent_id)
                
                return {
                    'success': True,
                    'operation': 'select',
                    'table_name': table_name,
                    'sql': sql,
                    'result': result,
                    'message': f'成功查询表 {table_name}'
                }
        
        return {
            'success': False,
            'error': f'无法解析查询命令: {query}'
        }
    
    def _handle_update(self, query: str, agent_id: str) -> Dict[str, Any]:
        """处理更新操作"""
        for pattern in self.table_patterns['update']:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                table_name = match.group(1)
                set_desc = match.group(2)
                where_desc = match.group(3)
                
                # 解析设置和条件
                set_data = self._parse_set_data(set_desc)
                where_condition = self._parse_where_condition(where_desc)
                
                if not set_data:
                    return {
                        'success': False,
                        'error': f'无法解析设置数据: {set_desc}'
                    }
                
                # 生成SQL
                sql = self._generate_update_sql(table_name, set_data, where_condition)
                
                # 执行SQL
                result = self.db_adapter.execute_sql(sql, agent_id)
                
                return {
                    'success': True,
                    'operation': 'update',
                    'table_name': table_name,
                    'sql': sql,
                    'result': result,
                    'message': f'成功更新表 {table_name}'
                }
        
        return {
            'success': False,
            'error': f'无法解析更新命令: {query}'
        }
    
    def _handle_delete(self, query: str, agent_id: str) -> Dict[str, Any]:
        """处理删除操作"""
        for pattern in self.table_patterns['delete']:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                table_name = match.group(1)
                where_desc = match.group(2)
                
                # 解析条件
                where_condition = self._parse_where_condition(where_desc)
                
                # 生成SQL
                sql = self._generate_delete_sql(table_name, where_condition)
                
                # 执行SQL
                result = self.db_adapter.execute_sql(sql, agent_id)
                
                return {
                    'success': True,
                    'operation': 'delete',
                    'table_name': table_name,
                    'sql': sql,
                    'result': result,
                    'message': f'成功删除表 {table_name} 中的数据'
                }
        
        return {
            'success': False,
            'error': f'无法解析删除命令: {query}'
        }
    
    def _parse_fields(self, fields_desc: str) -> List[Tuple[str, str]]:
        """解析字段定义"""
        fields = []
        field_parts = re.split(r'[,，]', fields_desc)
        
        for part in field_parts:
            part = part.strip()
            if ':' in part:
                field_name, field_type = part.split(':', 1)
                field_name = field_name.strip()
                field_type = field_type.strip()
                
                # 映射类型
                mapped_type = self.type_mapping.get(field_type.lower(), 'TEXT')
                fields.append((field_name, mapped_type))
        
        return fields
    
    def _parse_insert_data(self, data_desc: str) -> Dict[str, Any]:
        """解析插入数据"""
        data = {}
        pairs = re.split(r'[,，]', data_desc)
        
        for pair in pairs:
            pair = pair.strip()
            if '=' in pair:
                key, value = pair.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                data[key] = value
        
        return data
    
    def _parse_select_fields(self, fields_desc: str) -> List[str]:
        """解析查询字段"""
        if fields_desc.lower() in ['所有', '全部', 'all', '*']:
            return ['*']
        
        fields = []
        field_parts = re.split(r'[,，]', fields_desc)
        
        for part in field_parts:
            field = part.strip()
            if field:
                fields.append(field)
        
        return fields if fields else ['*']
    
    def _parse_set_data(self, set_desc: str) -> Dict[str, Any]:
        """解析设置数据"""
        return self._parse_insert_data(set_desc)
    
    def _parse_where_condition(self, where_desc: str) -> str:
        """解析WHERE条件"""
        # 简单的条件解析，支持基本的比较操作
        where_desc = where_desc.strip()
        
        # 替换中文操作符
        where_desc = where_desc.replace('等于', '=')
        where_desc = where_desc.replace('不等于', '!=')
        where_desc = where_desc.replace('大于', '>')
        where_desc = where_desc.replace('小于', '<')
        where_desc = where_desc.replace('大于等于', '>=')
        where_desc = where_desc.replace('小于等于', '<=')
        
        return where_desc
    
    def _generate_create_sql(self, table_name: str, fields: List[Tuple[str, str]]) -> str:
        """生成创建表SQL"""
        field_definitions = []
        for field_name, field_type in fields:
            field_definitions.append(f"{field_name} {field_type}")
        
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(field_definitions)})"
        return sql
    
    def _generate_insert_sql(self, table_name: str, data: Dict[str, Any]) -> str:
        """生成插入SQL"""
        columns = list(data.keys())
        values = list(data.values())
        
        # 处理字符串值
        formatted_values = []
        for value in values:
            if isinstance(value, str) and not value.isdigit():
                formatted_values.append(f"'{value}'")
            else:
                formatted_values.append(str(value))
        
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(formatted_values)})"
        return sql
    
    def _generate_select_sql(self, table_name: str, fields: List[str]) -> str:
        """生成查询SQL"""
        fields_str = ', '.join(fields)
        sql = f"SELECT {fields_str} FROM {table_name}"
        return sql
    
    def _generate_update_sql(self, table_name: str, set_data: Dict[str, Any], where_condition: str) -> str:
        """生成更新SQL"""
        set_parts = []
        for key, value in set_data.items():
            if isinstance(value, str) and not value.isdigit():
                set_parts.append(f"{key} = '{value}'")
            else:
                set_parts.append(f"{key} = {value}")
        
        sql = f"UPDATE {table_name} SET {', '.join(set_parts)}"
        if where_condition:
            sql += f" WHERE {where_condition}"
        
        return sql
    
    def _generate_delete_sql(self, table_name: str, where_condition: str) -> str:
        """生成删除SQL"""
        sql = f"DELETE FROM {table_name}"
        if where_condition:
            sql += f" WHERE {where_condition}"
        
        return sql


def natural_language_query(query: str, db_manager, agent_id: str = "nl_agent") -> Dict[str, Any]:
    """
    自然语言查询接口
    
    Args:
        query: 自然语言查询
        db_manager: 数据库管理器
        agent_id: 代理ID
        
    Returns:
        查询结果
    """
    processor = NaturalLanguageProcessor(db_manager)
    return processor.process_natural_language(query, agent_id) 