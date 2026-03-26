"""
搜索基础类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseSearch(ABC):
    """搜索基础类"""
    
    @abstractmethod
    def search(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        执行搜索
        
        Args:
            query: 搜索关键词
            count: 返回结果数量
        
        Returns:
            搜索结果列表，每个结果包含：
            - title: 标题
            - url: 链接
            - snippet: 摘要
            - source: 来源
        """
        pass
