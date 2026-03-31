"""
节点3: 深度搜索（获取事实依据和数据支撑）
"""
from typing import Dict, Any
from datetime import datetime, timedelta
from langchain_core.runnables import RunnableConfig
from core.state import GlobalState
from search import create_search
from utils.logger import logger


def deep_search_node(state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
    """
    深度搜索相关内容（获取事实依据、数据和案例）
    
    Args:
        state: 全局状态
        config: 运行配置
    
    Returns:
        更新后的状态
    """
    logger.info("="*60)
    logger.info("🚀 节点3: 深度搜索（获取事实依据）")
    logger.info("="*60)
    
    topic = state.topic
    logger.info(f"📝 深度搜索主题: {topic}")
    
    try:
        # 创建搜索实例
        search = create_search()
        
        # 时效性过滤：只搜索最近7天的内容
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        date_filter = f"after:{start_date.strftime('%Y-%m-%d')}"
        
        # 围绕主题搜索（添加时效性和数据要求）
        query = f"{topic} 数据 案例 研究 {date_filter}"
        logger.info(f"   搜索查询: {query}")
        logger.info(f"   时间范围: {start_date.strftime('%Y-%m-%d')} 至今")
        
        results = search.search(query, count=8)
        
        logger.info(f"✅ 找到 {len(results)} 条深度内容")
        
        for i, item in enumerate(results[:3], 1):
            logger.info(f"   {i}. {item['title'][:50]}...")
        
        logger.info("="*60)
        logger.info("✅ 节点3完成")
        logger.info("="*60)
        
        return {
            "deep_search_results": results
        }
        
    except Exception as e:
        logger.error(f"❌ 深度搜索失败: {e}")
        return {
            "deep_search_results": []
        }
