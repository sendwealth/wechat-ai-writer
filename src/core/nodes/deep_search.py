"""
节点3: 深度搜索
"""
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from core.state import GlobalState
from search import create_search
from utils.logger import logger


def deep_search_node(state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
    """
    深度搜索相关内容
    
    Args:
        state: 全局状态
        config: 运行配置
    
    Returns:
        更新后的状态
    """
    logger.info("="*60)
    logger.info("🚀 节点3: 深度搜索")
    logger.info("="*60)
    
    topic = state.topic
    logger.info(f"📝 深度搜索主题: {topic}")
    
    try:
        # 创建搜索实例
        search = create_search()
        
        # 围绕主题搜索
        query = f"{topic} 详细 案例 应用 2026"
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
