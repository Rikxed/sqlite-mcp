#!/usr/bin/env python3
"""
自然语言MCP服务器主程序
支持自然语言建表和查询
"""

import asyncio
import logging
import sys
from mcp.natural_language_server import create_natural_language_server
from config.settings import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    try:
        logger.info("启动自然语言MCP服务器...")
        logger.info(f"数据库路径: {settings.database_path}")
        
        # 创建服务器实例
        server = create_natural_language_server()
        
        # 运行服务器
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("服务器被用户中断")
    except Exception as e:
        logger.error(f"服务器运行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 