"""
日志系统 - 基于 loguru
"""
import sys
from pathlib import Path
from loguru import logger

# 移除默认处理器
logger.remove()

# 添加控制台输出
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)

# 添加文件输出
log_dir = Path(__file__).parent.parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logger.add(
    log_dir / "app.log",
    rotation="100 MB",
    retention="30 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    encoding="utf-8"
)


def get_logger(name: str):
    """获取指定名称的 logger"""
    return logger.bind(name=name)


# 导出
__all__ = ["logger", "get_logger"]
