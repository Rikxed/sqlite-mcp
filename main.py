"""
SQLite MCP服务器主程序 - 标准stdio模式
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

from config.settings import settings
from mcp.simple_server import create_simple_server

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),  # 日志输出到stderr
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """主函数 - 标准stdio MCP服务器"""
    try:
        logger.info("启动SQLite MCP服务器 (stdio模式)...")
        logger.info(f"服务器名称: {settings.mcp_server_name}")
        logger.info(f"服务器版本: {settings.mcp_server_version}")
        logger.info(f"数据库路径: {settings.database_path}")
        
        if settings.init_script:
            logger.info(f"初始化脚本: {settings.init_script}")
        
        # 创建并运行MCP服务器
        server = create_simple_server()
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("服务器被用户中断")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 