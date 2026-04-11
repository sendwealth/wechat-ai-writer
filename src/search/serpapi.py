"""
SerpAPI 搜索集成
"""
import os
from typing import List, Dict, Any
from serpapi import GoogleSearch
from search.base import BaseSearch
from utils.logger import logger


class SerpAPISearch(BaseSearch):
    """SerpAPI 搜索"""

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_KEY 未配置")
    
    def search(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """执行搜索"""
        logger.info(f"SerpAPI 搜索: {query}")
        
        try:
            search = GoogleSearch({
                "q": query,
                "api_key": self.api_key,
                "num": count,
                "hl": "zh-cn",
                "gl": "cn"
            })
            
            results = search.get_dict()
            organic_results = results.get("organic_results", [])
            
            articles = []
            for item in organic_results[:count]:
                articles.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("source", ""),
                    "position": item.get("position", 0)
                })
            
            logger.info(f"找到 {len(articles)} 条结果")
            return articles
            
        except Exception as e:
            logger.error(f"SerpAPI 搜索失败: {e}")
            return []
