"""
重试装饰器 - 指数退避
"""
import time
import functools
from typing import Type, Tuple
from utils.logger import logger


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    重试装饰器（指数退避）

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟（秒）
        exceptions: 需要重试的异常类型
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"⚠️ {func.__name__} 第{attempt+1}次失败: {e}，"
                            f"{delay:.1f}s 后重试..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"❌ {func.__name__} 重试{max_retries}次后仍失败: {e}"
                        )
            raise last_error
        return wrapper
    return decorator
