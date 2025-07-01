#!/usr/bin/env python3
"""
简化版MCP服务器 - 用于测试Docker环境
"""
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp.enhanced_server import create_enhanced_server

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """主函数 - 简化版MCP服务器"""
    try:
        logger.info("启动简化版MCP服务器...")
        logger.info("服务器将在stdio模式下运行")
        
        # 创建MCP服务器实例
        server = create_enhanced_server()
        
        # 输出启动信息到stderr（不影响stdio通信）
        logger.info("✅ MCP服务器启动成功，等待客户端连接...")
        logger.info("📝 服务器运行在stdio模式下")
        logger.info("🔄 服务器将保持运行状态...")
        
        # 运行服务器
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("服务器被用户中断")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 