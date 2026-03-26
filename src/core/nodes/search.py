"""
节点1: 搜索科技新闻
"""
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from core.state import GlobalState
from search import create_search
from utils.logger import logger


def search_tech_news_node(state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
    """
    搜索科技新闻
    
    Args:
        state: 全局状态
        config: 运行配置
    
    Returns:
        更新后的状态
    """
    logger.info("="*60)
    logger.info("🚀 节点1: 搜索科技新闻")
    logger.info("="*60)
    
    keyword = state.topic_keyword
    logger.info(f"📝 搜索关键词: {keyword}")
    
    try:
        # 创建搜索实例
        search = create_search()
        
        # 搜索新闻
        query = f"{keyword} 最新 科技 新闻 2026"
        articles = search.search(query, count=10)
        
        if not articles:
            logger.warning("未找到相关文章")
            return {
                "raw_articles": [],
                "selected_article": {}
            }
        
        # 选择第一篇最权威的文章
        selected = articles[0]
        logger.info(f"✅ 选中文章: {selected['title']}")
        logger.info(f"   来源: {selected['source']}")
        
        logger.info("="*60)
        logger.info("✅ 节点1完成")
        logger.info("="*60)
        
        return {
            "raw_articles": articles,
            "selected_article": selected
        }
        
    except Exception as e:
        logger.error(f"❌ 搜索失败: {e}")
        return {
            "raw_articles": [],
            "selected_article": {}
        }
