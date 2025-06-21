#!/usr/bin/env python3
"""
自然语言MCP服务器使用示例
演示如何使用自然语言进行数据库操作
"""

import asyncio
import json
import logging
from mcp.natural_language_server import create_natural_language_server

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_natural_language_operations():
    """测试自然语言操作"""
    server = create_natural_language_server()
    
    # 测试用例
    test_cases = [
        {
            "name": "自然语言建表 - 用户表",
            "tool": "natural_language_create_table",
            "arguments": {
                "description": "创建一个用户表，包含姓名、年龄、邮箱字段"
            }
        },
        {
            "name": "自然语言建表 - 产品表",
            "tool": "natural_language_create_table",
            "arguments": {
                "description": "创建一个产品表，包含名称、价格、分类字段"
            }
        },
        {
            "name": "自然语言插入 - 用户数据",
            "tool": "natural_language_insert",
            "arguments": {
                "description": "向用户表插入一个叫张三的用户，年龄25岁"
            }
        },
        {
            "name": "自然语言插入 - 产品数据",
            "tool": "natural_language_insert",
            "arguments": {
                "description": "向产品表插入一个叫笔记本电脑的产品，价格5999元"
            }
        },
        {
            "name": "自然语言查询 - 查询用户",
            "tool": "natural_language_query",
            "arguments": {
                "description": "查询所有年龄大于20的用户"
            }
        },
        {
            "name": "自然语言更新 - 更新用户年龄",
            "tool": "natural_language_update",
            "arguments": {
                "description": "将用户张三的年龄改为26岁"
            }
        },
        {
            "name": "列出所有表",
            "tool": "list_tables",
            "arguments": {}
        },
        {
            "name": "数据库信息",
            "tool": "database_info",
            "arguments": {}
        }
    ]
    
    print("=== 自然语言MCP服务器测试 ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试 {i}: {test_case['name']}")
        print(f"工具: {test_case['tool']}")
        print(f"参数: {json.dumps(test_case['arguments'], ensure_ascii=False, indent=2)}")
        
        try:
            # 构造请求
            request = {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": test_case['tool'],
                    "arguments": test_case['arguments']
                }
            }
            
            # 处理请求
            response = await server.handle_request(request)
            
            # 显示结果
            if "result" in response:
                content = response["result"].get("content", [])
                if content:
                    print(f"结果: {content[0].get('text', '')}")
                else:
                    print("结果: 无内容")
            elif "error" in response:
                print(f"错误: {response['error']['message']}")
            
        except Exception as e:
            print(f"执行失败: {e}")
        
        print("-" * 50)


async def test_sql_operations():
    """测试SQL操作"""
    server = create_natural_language_server()
    
    sql_test_cases = [
        {
            "name": "SQL查询 - 查询所有用户",
            "tool": "sql_query",
            "arguments": {
                "query": "SELECT * FROM 用户"
            }
        },
        {
            "name": "SQL插入 - 插入用户数据",
            "tool": "sql_update",
            "arguments": {
                "query": "INSERT INTO 用户 (姓名, 年龄, 邮箱) VALUES (?, ?, ?)",
                "params": ["李四", 30, "lisi@example.com"]
            }
        },
        {
            "name": "SQL更新 - 更新产品价格",
            "tool": "sql_update",
            "arguments": {
                "query": "UPDATE 产品 SET 价格 = ? WHERE 名称 = ?",
                "params": [5500, "笔记本电脑"]
            }
        }
    ]
    
    print("\n=== SQL操作测试 ===\n")
    
    for i, test_case in enumerate(sql_test_cases, 1):
        print(f"SQL测试 {i}: {test_case['name']}")
        print(f"SQL: {test_case['arguments']['query']}")
        
        try:
            request = {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": test_case['tool'],
                    "arguments": test_case['arguments']
                }
            }
            
            response = await server.handle_request(request)
            
            if "result" in response:
                content = response["result"].get("content", [])
                if content:
                    print(f"结果: {content[0].get('text', '')}")
            elif "error" in response:
                print(f"错误: {response['error']['message']}")
                
        except Exception as e:
            print(f"执行失败: {e}")
        
        print("-" * 50)


async def main():
    """主函数"""
    try:
        # 测试自然语言操作
        await test_natural_language_operations()
        
        # 测试SQL操作
        await test_sql_operations()
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 