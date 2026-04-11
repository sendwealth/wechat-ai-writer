"""
搜索工厂
"""
import os
from typing import Dict, Any
from search.base import BaseSearch
from search.serpapi import SerpAPISearch


def create_search() -> BaseSearch:
    """创建搜索实例"""
    provider = os.getenv("SEARCH_PROVIDER", "serpapi")

    if provider == "serpapi":
        return SerpAPISearch()
    else:
        raise ValueError(f"不支持的搜索提供商: {provider}")
