"""
节点1: 搜索科技新闻（时效性优先）
"""
from typing import Dict, Any
from datetime import datetime, timedelta
from langchain_core.runnables import RunnableConfig
from core.state import GlobalState
from search import create_search
from utils.logger import logger


def search_tech_news_node(state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
    """
    搜索科技新闻（时效性优先，限定最近7天）
    
    Args:
        state: 全局状态
        config: 运行配置
    
    Returns:
        更新后的状态
    """
    logger.info("="*60)
    logger.info("🚀 节点1: 搜索科技新闻（时效性优先）")
    logger.info("="*60)
    
    keyword = state.topic_keyword
    logger.info(f"📝 搜索关键词: {keyword}")
    
    try:
        # 创建搜索实例
        search = create_search()
        
        # 时效性过滤：只搜索最近7天的新闻
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        date_filter = f"after:{start_date.strftime('%Y-%m-%d')}"
        
        # 搜索新闻（添加时效性过滤）
        query = f"{keyword} 最新 {date_filter}"
        logger.info(f"   搜索查询: {query}")
        logger.info(f"   时间范围: {start_date.strftime('%Y-%m-%d')} 至今")
        
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
