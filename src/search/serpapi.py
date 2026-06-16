"""
SerpAPI 搜索集成（兼容 serpapi>=1.0 新版 API）
"""
import os
from typing import List, Dict, Any

import serpapi
from search.base import BaseSearch
from utils.logger import logger


class SerpAPISearch(BaseSearch):
    """SerpAPI 搜索"""

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_KEY 未配置")

    def search(self, query: str, count: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """执行普通搜索"""
        logger.info(f"SerpAPI 搜索: {query}")

        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": count,
                "hl": "zh-cn",
                "gl": "cn",
            }
            params.update(kwargs)

            client = serpapi.Client(api_key=self.api_key)
            results = client.search(params)
            # SerpResults 兼容 dict 访问
            organic_results = results.get("organic_results", []) if hasattr(results, 'get') else results["organic_results"]

            articles = []
            for item in organic_results[:count]:
                articles.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("source", ""),
                    "position": item.get("position", 0),
                })

            logger.info(f"找到 {len(articles)} 条结果")
            return articles

        except Exception as e:
            logger.error(f"SerpAPI 搜索失败: {e}")
            return []

    def search_news(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """使用 Google News 引擎搜索最新新闻"""
        logger.info(f"SerpAPI News 搜索: {query}")

        try:
            params = {
                "engine": "google_news",
                "q": query,
                "api_key": self.api_key,
                "num": count,
                "hl": "zh-cn",
                "gl": "cn",
            }

            client = serpapi.Client(api_key=self.api_key)
            results = client.search(params)
            news_results = results.get("news_results", []) if hasattr(results, 'get') else results.get("news_results", [])

            articles = []
            for item in news_results[:count]:
                if "stories" in item and isinstance(item["stories"], list):
                    for story in item["stories"]:
                        articles.append({
                            "title": story.get("title", ""),
                            "url": story.get("link", ""),
                            "snippet": story.get("snippet", ""),
                            "source": story.get("source", {}).get("name", "") if isinstance(story.get("source"), dict) else str(story.get("source", "")),
                            "date": story.get("date", ""),
                            "position": len(articles),
                        })
                else:
                    source = item.get("source", "")
                    if isinstance(source, dict):
                        source = source.get("name", "")
                    articles.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": str(source),
                        "date": item.get("date", ""),
                        "position": len(articles),
                    })

            logger.info(f"News 找到 {len(articles)} 条结果")
            return articles

        except Exception as e:
            logger.error(f"SerpAPI News 搜索失败: {e}")
            return []
