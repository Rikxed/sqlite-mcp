#!/usr/bin/env python3
"""
标准MCP服务器主程序
支持完整的MCP协议 (2024-11-05)
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp.standard_server import create_standard_server
from config.settings import settings

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    try:
        logger.info(f"启动标准MCP服务器 (stdio模式)...")
        logger.info(f"服务器名称: {settings.server_name}")
        logger.info(f"服务器版本: {settings.server_version}")
        logger.info(f"数据库路径: {settings.database_path}")
        logger.info(f"初始化脚本: {settings.init_script}")
        
        # 创建标准MCP服务器
        server = create_standard_server()
        
        # 运行服务器
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("服务器被用户中断")
    except Exception as e:
        logger.error(f"服务器运行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 