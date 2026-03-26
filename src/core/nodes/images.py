"""
节点5: 生成图片
"""
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from core.state import GlobalState
from utils.logger import logger


def generate_images_node(state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
    """
    生成配图
    
    Args:
        state: 全局状态
        config: 运行配置
    
    Returns:
        更新后的状态
    """
    logger.info("="*60)
    logger.info("🚀 节点5: 生成图片")
    logger.info("="*60)
    
    topic = state.topic
    logger.info(f"📝 为主题生成配图: {topic}")
    
    # TODO: 集成真实图片生成API（DALL-E / Stable Diffusion）
    # 当前使用占位符
    
    images = []
    for i in range(2):
        images.append({
            "url": f"https://via.placeholder.com/800x400?text={topic}+Image+{i+1}",
            "alt": f"{topic} 配图 {i+1}",
            "position": i
        })
    
    logger.info(f"✅ 生成 {len(images)} 张配图")
    
    logger.info("="*60)
    logger.info("✅ 节点5完成")
    logger.info("="*60)
    
    return {
        "article_images": images
    }
