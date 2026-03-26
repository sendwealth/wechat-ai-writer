"""
搜索工厂
"""
from typing import Dict, Any
from search.base import BaseSearch
from search.serpapi import SerpAPISearch
from utils.config import config


def create_search() -> BaseSearch:
    """创建搜索实例"""
    provider = config.get_search_provider()
    
    if provider == "serpapi":
        return SerpAPISearch()
    else:
        raise ValueError(f"不支持的搜索提供商: {provider}")
