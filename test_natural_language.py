#!/usr/bin/env python3
"""
自然语言建表测试脚本
演示如何使用自然语言创建数据库表
"""

import asyncio
import json
import logging
from mcp.natural_language_server import create_natural_language_server

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_natural_language_create_table():
    """测试自然语言建表功能"""
    server = create_natural_language_server()
    
    # 测试用例
    test_cases = [
        {
            "name": "用户表",
            "description": "创建一个用户表，包含姓名、年龄、邮箱字段"
        },
        {
            "name": "产品表", 
            "description": "创建一个产品表，包含名称、价格、分类字段"
        },
        {
            "name": "订单表",
            "description": "创建一个订单表，包含订单ID、用户ID、产品ID、数量、总价、创建时间字段"
        }
    ]
    
    print("=== 自然语言建表测试 ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试 {i}: {test_case['name']}")
        print(f"描述: {test_case['description']}")
        
        try:
            # 构造MCP请求
            request = {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": "natural_language_create_table",
                    "arguments": {
                        "description": test_case['description']
                    }
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


async def test_natural_language_query():
    """测试自然语言查询功能"""
    server = create_natural_language_server()
    
    # 先创建一些测试数据
    print("=== 创建测试数据 ===")
    
    # 创建用户表
    create_table_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "natural_language_create_table",
            "arguments": {
                "description": "创建一个用户表，包含姓名、年龄、邮箱字段"
            }
        }
    }
    
    await server.handle_request(create_table_request)
    
    # 插入测试数据
    insert_requests = [
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "natural_language_insert",
                "arguments": {
                    "description": "向用户表插入一个叫张三的用户，年龄25岁"
                }
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "natural_language_insert",
                "arguments": {
                    "description": "向用户表插入一个叫李四的用户，年龄30岁"
                }
            }
        }
    ]
    
    for request in insert_requests:
        await server.handle_request(request)
    
    # 测试查询
    print("\n=== 自然语言查询测试 ===")
    
    query_test_cases = [
        {
            "name": "查询所有用户",
            "description": "查询所有用户"
        },
        {
            "name": "查询年龄大于20的用户",
            "description": "查询所有年龄大于20的用户"
        }
    ]
    
    for i, test_case in enumerate(query_test_cases, 1):
        print(f"查询 {i}: {test_case['name']}")
        print(f"描述: {test_case['description']}")
        
        try:
            request = {
                "jsonrpc": "2.0",
                "id": i + 10,
                "method": "tools/call",
                "params": {
                    "name": "natural_language_query",
                    "arguments": {
                        "description": test_case['description']
                    }
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


async def interactive_test():
    """交互式测试"""
    server = create_natural_language_server()
    
    print("=== 交互式自然语言建表测试 ===")
    print("输入 'quit' 退出")
    print("输入 'help' 查看帮助")
    print()
    
    while True:
        try:
            user_input = input("请输入自然语言描述: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'help':
                print("""
可用命令:
- 建表: "创建一个xxx表，包含xxx字段"
- 查询: "查询所有xxx"
- 插入: "向xxx表插入xxx"
- 更新: "将xxx的xxx改为xxx"
- 列表: "列出所有表"
- 信息: "获取数据库信息"
                """)
                continue
            elif not user_input:
                continue
            
            # 判断操作类型
            if "创建" in user_input and "表" in user_input:
                tool_name = "natural_language_create_table"
            elif "查询" in user_input or "查找" in user_input or "搜索" in user_input:
                tool_name = "natural_language_query"
            elif "插入" in user_input:
                tool_name = "natural_language_insert"
            elif "改为" in user_input or "更新" in user_input:
                tool_name = "natural_language_update"
            elif "列出" in user_input and "表" in user_input:
                tool_name = "list_tables"
            elif "信息" in user_input:
                tool_name = "database_info"
            else:
                print("无法识别操作类型，请使用 'help' 查看帮助")
                continue
            
            # 构造请求
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": {
                        "description": user_input
                    } if tool_name.startswith("natural_language") else {}
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
            
        except KeyboardInterrupt:
            print("\n退出测试")
            break
        except Exception as e:
            print(f"执行失败: {e}")


async def main():
    """主函数"""
    try:
        print("选择测试模式:")
        print("1. 自动测试自然语言建表")
        print("2. 自动测试自然语言查询")
        print("3. 交互式测试")
        
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == "1":
            await test_natural_language_create_table()
        elif choice == "2":
            await test_natural_language_query()
        elif choice == "3":
            await interactive_test()
        else:
            print("无效选择，运行默认测试")
            await test_natural_language_create_table()
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 