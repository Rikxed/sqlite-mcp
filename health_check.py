#!/usr/bin/env python3
"""
MCP服务器健康检查脚本
用于验证MCP服务器是否正常运行并响应请求
"""

import asyncio
import json
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp.enhanced_server import create_enhanced_server

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def health_check():
    """执行健康检查"""
    try:
        # 创建MCP服务器实例
        server = create_enhanced_server()
        
        # 测试初始化
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "clientInfo": {
                    "name": "health-check",
                    "version": "1.0.0"
                }
            }
        }
        
        init_response = await server.handle_request(init_request)
        
        if "error" in init_response:
            logger.error(f"初始化失败: {init_response['error']}")
            return False
        
        # 测试工具列表
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        tools_response = await server.handle_request(tools_request)
        
        if "error" in tools_response:
            logger.error(f"获取工具列表失败: {tools_response['error']}")
            return False
        
        # 测试数据库连接
        db_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "database_info",
                "arguments": {}
            }
        }
        
        db_response = await server.handle_request(db_request)
        
        if "error" in db_response:
            logger.error(f"数据库连接失败: {db_response['error']}")
            return False
        
        logger.info("✅ 健康检查通过")
        return True
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return False


def main():
    """主函数"""
    try:
        # 运行健康检查
        result = asyncio.run(health_check())
        
        if result:
            print("✅ MCP服务器健康检查通过")
            sys.exit(0)
        else:
            print("❌ MCP服务器健康检查失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"健康检查过程中出错: {e}")
        print(f"❌ 健康检查异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 