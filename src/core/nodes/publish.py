"""
节点7: 发布到微信 - 自动获取 Token
"""
import os
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from core.state import GlobalState
from wechat.client import WeChatClient
from utils.logger import logger


def publish_to_wechat_node(state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
    """
    发布到微信公众号 - 自动管理 Access Token
    
    Args:
        state: 全局状态
        config: 运行配置
    
    Returns:
        更新后的状态
    """
    logger.info("="*60)
    logger.info("🚀 节点7: 发布到微信")
    logger.info("="*60)
    
    # 检查是否为测试模式
    dry_run = state.dry_run
    
    if dry_run:
        logger.info("⚠️  测试模式，跳过发布")
        logger.info("="*60)
        logger.info("✅ 节点7完成（测试模式）")
        logger.info("="*60)
        return {
            "publish_result": {"status": "dry_run", "message": "测试模式，未发布"},
            "publish_success": True
        }
    
    # 检查配置
    wechat_config = state.wechat_config
    appid = wechat_config.get("appid") or os.getenv("WECHAT_APPID")
    appsecret = wechat_config.get("appsecret") or os.getenv("WECHAT_APPSECRET")
    access_token = wechat_config.get("access_token") or os.getenv("WECHAT_ACCESS_TOKEN")
    
    if not (access_token or (appid and appsecret)):
        logger.error("❌ 未配置微信凭证")
        logger.error("   请配置 WECHAT_ACCESS_TOKEN 或 (WECHAT_APPID + WECHAT_APPSECRET)")
        return {
            "publish_result": {"error": "未配置微信凭证"},
            "publish_success": False
        }
    
    try:
        # 创建微信客户端（自动管理 Token）
        client = WeChatClient(
            appid=appid,
            appsecret=appsecret,
            access_token=access_token
        )
        
        # 构建文章数据
        article_data = {
            "title": state.topic,
            "content": state.article_with_images,
            "thumb_media_id": "placeholder",  # TODO: 需要先上传封面图
            "author": "AI Writer",
            "digest": state.topic,
            "content_source_url": "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }
        
        logger.info(f"📝 创建草稿: {state.topic}")
        logger.info(f"   Token 管理方式: {'自动获取' if (appid and appsecret) else '静态配置'}")
        
        # 创建草稿
        media_id = client.add_draft([article_data])
        logger.info(f"✅ 草稿创建成功: {media_id}")
        
        # 发布草稿
        logger.info("📤 发布草稿...")
        publish_id = client.publish(media_id)
        logger.info(f"✅ 发布成功: {publish_id}")
        
        logger.info("="*60)
        logger.info("✅ 节点7完成")
        logger.info("="*60)
        
        return {
            "publish_result": {
                "media_id": media_id,
                "publish_id": publish_id
            },
            "publish_success": True
        }
        
    except Exception as e:
        logger.error(f"❌ 发布失败: {e}")
        return {
            "publish_result": {"error": str(e)},
            "publish_success": False
        }
