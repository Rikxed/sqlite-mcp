"""
应用配置管理模块
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 数据库配置
    database_path: str = os.getenv("DATABASE_PATH", "data/sqlite.db")
    
    # 初始化配置
    init_script: Optional[str] = os.getenv("INIT_SCRIPT")
    
    # 日志配置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # MCP配置
    mcp_server_name: str = "sqlite-mcp-server"
    mcp_server_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings() 