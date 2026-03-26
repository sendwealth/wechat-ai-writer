"""
节点5: 生成图片 - 支持环境变量配置
"""
import os
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from core.state import GlobalState
from image import generate_article_images
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
    highlights = state.highlights
    
    logger.info(f"📝 为主题生成配图: {topic}")
    logger.info(f"💡 文章亮点: {len(highlights)} 个")
    
    # 获取图片生成配置（从环境变量读取）
    image_provider = os.getenv("IMAGE_PROVIDER", "placeholder")
    num_images = int(os.getenv("NUM_IMAGES", "2"))
    
    logger.info(f"🎨 图片生成提供商: {image_provider}")
    logger.info(f"📊 生成数量: {num_images} 张")
    
    # 生成图片
    images = generate_article_images(
        topic=topic,
        highlights=highlights,
        num_images=num_images,
        provider=image_provider
    )
    
    # 统计
    success_count = sum(1 for img in images if not img.get("fallback", False))
    fallback_count = len(images) - success_count
    
    logger.info(f"✅ 生成完成: {success_count} 张成功, {fallback_count} 张使用占位符")
    
    # 显示成本
    if image_provider == "dalle3":
        cost = success_count * 0.04  # $0.04/张
        logger.info(f"💰 成本: ${cost:.2f} (DALL-E 3)")
    elif image_provider == "cogview":
        cost = success_count * 0.06  # ¥0.06/张
        logger.info(f"💰 成本: ¥{cost:.2f} (CogView)")
    
    logger.info("="*60)
    logger.info("✅ 节点5完成")
    logger.info("="*60)
    
    return {
        "article_images": images
    }
