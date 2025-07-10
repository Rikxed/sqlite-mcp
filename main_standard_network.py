"""
标准MCP网络服务器主程序 - 使用标准MCP网络协议
兼容标准MCP客户端
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

from config.settings import settings
from mcp.standard_network_server import create_standard_network_server

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
    """主函数 - 标准MCP网络服务器"""
    try:
        # 获取环境变量配置
        agent_id = os.getenv("AGENT_ID")
        use_thread_safe = os.getenv("USE_THREAD_SAFE", "false").lower() == "true"
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))
        
        logger.info("启动标准MCP网络服务器...")
        logger.info(f"服务器名称: {settings.mcp_server_name}")
        logger.info(f"服务器版本: {settings.mcp_server_version}")
        logger.info(f"数据库路径: {settings.database_path}")
        logger.info(f"Agent ID: {agent_id or '自动生成'}")
        logger.info(f"线程安全模式: {use_thread_safe}")
        logger.info(f"监听地址: {host}:{port}")
        
        if settings.init_script:
            logger.info(f"初始化脚本: {settings.init_script}")
        
        # 创建并运行标准MCP网络服务器
        server = create_standard_network_server(agent_id, use_thread_safe)
        await server.run(host, port)
        
    except KeyboardInterrupt:
        logger.info("服务器被用户中断")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 