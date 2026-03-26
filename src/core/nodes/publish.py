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
        
        # 读取封面 media_id
        cover_media_id = None
        cover_file = "/root/.openclaw/workspace/wechat-ai-writer/.cover_media_id"
        if os.path.exists(cover_file):
            with open(cover_file, 'r') as f:
                cover_media_id = f.read().strip()
        
        if not cover_media_id:
            logger.error("❌ 未找到封面 media_id")
            return {
                "publish_result": {"error": "未找到封面 media_id"},
                "publish_success": False
            }
        
        # 限制标题长度（微信公众号实际限制约 32 字节，约 10 个汉字）
        # 生成简短标题（智能截断）
        full_title = state.topic
        
        # 字节长度检查（限制为 32 字节）
        title_bytes = full_title.encode('utf-8')
        if len(title_bytes) <= 32:
            # 标题符合要求，直接使用
            title = full_title
        else:
            # 标题过长，智能截断：在标点符号处断开
            # 尝试在冒号、逗号、句号等标点处截断
            import re
            # 查找合适的截断点
            match = re.search(r'^.{10,30}?[：:,，。！？、]', full_title)
            if match:
                title = match.group(0)[:-1]  # 去掉最后的标点
                # 再次检查字节长度
                if len(title.encode('utf-8')) > 32:
                    # 仍然过长，继续截断
                    while len(title.encode('utf-8')) > 32 and len(title) > 0:
                        title = title[:-1]
            else:
                # 没有合适的标点，简单截断
                while len(title_bytes) > 32 and len(full_title) > 0:
                    full_title = full_title[:-1]
                    title_bytes = full_title.encode('utf-8')
                title = full_title
            
            logger.info(f"   标题已优化: {title}")
        
        logger.info(f"   标题字节长度: {len(title.encode('utf-8'))}")
        logger.info(f"   标题字符长度: {len(title)}")
        
        # 构建文章数据
        article_data = {
            "title": title,
            "content": state.article_with_images,
            "thumb_media_id": cover_media_id,  # 使用已上传的封面
            "author": "AI Writer",
            "digest": title[:30] if len(title) > 30 else title,  # 摘要最多 40 字节
            "content_source_url": "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }
        
        logger.info(f"📝 创建草稿: {title}")
        logger.info(f"   Token 管理方式: {'自动获取' if (appid and appsecret) else '静态配置'}")
        logger.info(f"   标题长度: {len(title.encode('utf-8'))} 字节")
        logger.info(f"   摘要长度: {len(article_data['digest'].encode('utf-8'))} 字节")
        
        # 创建草稿
        media_id = client.add_draft([article_data])
        logger.info(f"✅ 草稿创建成功: {media_id}")
        
        # 发布草稿（需要认证服务号权限）
        logger.info("📤 尝试发布草稿...")
        try:
            publish_id = client.publish(media_id)
            logger.info(f"✅ 发布成功: {publish_id}")
            publish_result = {
                "media_id": media_id,
                "publish_id": publish_id
            }
        except Exception as e:
            # 如果发布失败，返回草稿 ID（可手动发布）
            logger.warning(f"⚠️  自动发布失败（可能需要认证服务号）: {e}")
            logger.info(f"💡 草稿已创建，可在公众号后台手动发布")
            publish_result = {
                "media_id": media_id,
                "status": "draft_only",
                "message": "草稿已创建，请在公众号后台手动发布"
            }
        
        logger.info("="*60)
        logger.info("✅ 节点7完成")
        logger.info("="*60)
        
        return {
            "publish_result": publish_result,
            "publish_success": True  # 草稿创建成功即为成功
        }
        
    except Exception as e:
        logger.error(f"❌ 发布失败: {e}")
        return {
            "publish_result": {"error": str(e)},
            "publish_success": False
        }
