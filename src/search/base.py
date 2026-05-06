"""
搜索基础类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseSearch(ABC):
    """搜索基础类"""

    @abstractmethod
    def search(self, query: str, count: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        执行搜索

        Args:
            query: 搜索关键词
            count: 返回结果数量
            **kwargs: 引擎特定参数（如 tbs="qdr:w"）

        Returns:
            搜索结果列表，每个结果包含：
            - title: 标题
            - url: 链接
            - snippet: 摘要
            - source: 来源
        """
        pass

    def search_news(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        搜索新闻（优先使用新闻引擎，不支持时 fallback 到普通搜索）

        Args:
            query: 搜索关键词
            count: 返回结果数量

        Returns:
            搜索结果列表，同 search() 格式，额外可能包含 date 字段
        """
        return self.search(query, count)
