"""
节点5: 生成图片 - 支持环境变量配置
"""
import os
import requests
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from core.state import GlobalState
from image import generate_article_images
from utils.logger import logger


def download_and_upload_to_wechat(image_url: str, wechat_client) -> str:
    """
    下载图片并上传到微信
    
    Args:
        image_url: 原始图片 URL
        wechat_client: 微信客户端
    
    Returns:
        微信图片 URL
    """
    try:
        # 下载图片
        logger.info(f"📥 下载图片: {image_url[:50]}...")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        image_data = response.content
        
        # 上传到微信
        wechat_url = wechat_client.upload_news_image(image_data)
        logger.info(f"✅ 图片已上传到微信: {wechat_url[:50]}...")
        
        return wechat_url
    except Exception as e:
        logger.error(f"❌ 上传图片到微信失败: {e}")
        return image_url  # 返回原始 URL


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
    
    # 如果是 CogView 或 DALL-E，需要上传到微信
    if image_provider in ["cogview", "dalle3"]:
        logger.info("📤 开始上传图片到微信...")
        from wechat.client import WeChatClient
        
        appid = os.getenv("WECHAT_APPID")
        appsecret = os.getenv("WECHAT_APPSECRET")
        
        if appid and appsecret:
            wechat_client = WeChatClient(appid, appsecret)
            
            for img in images:
                if not img.get("fallback", False):
                    try:
                        # 下载并上传到微信
                        wechat_url = download_and_upload_to_wechat(img["url"], wechat_client)
                        img["url"] = wechat_url
                    except Exception as e:
                        logger.warning(f"⚠️  图片上传失败，使用原始 URL: {e}")
    
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
