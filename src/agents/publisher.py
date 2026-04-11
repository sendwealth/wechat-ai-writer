"""
Agent: Publisher - 微信公众号发布
"""
import os
from langchain_core.runnables import RunnableConfig
from utils.config import config
from utils.logger import logger


def publisher_node(state: dict, run_config=None) -> dict:
    """发布到微信公众号"""
    dry_run = state.get("dry_run", False)
    article_html = state.get("article_html", "")
    title = state.get("selected_title", state.get("topic_keyword", "科技"))
    images = state.get("article_images", [])
    overall_score = state.get("overall_score", 0)

    logger.info(f"📤 Publisher: {'测试模式' if dry_run else '准备发布'}")
    logger.info(f"   标题: {title}")
    logger.info(f"   质量分: {overall_score}/10")

    if dry_run:
        logger.info("⚠️ 测试模式，跳过发布")
        return {
            "publish_result": {
                "status": "dry_run",
                "title": title,
                "score": overall_score,
                "article_length": len(article_html),
            },
            "publish_success": True,
        }

    if not article_html:
        logger.error("❌ 无文章内容")
        return {
            "publish_result": {"error": "无文章内容"},
            "publish_success": False,
            "errors": [{"node": "publisher", "error": "无文章内容", "severity": "FATAL", "timestamp": ""}],
        }

    try:
        from wechat.client import WeChatClient

        appid = os.getenv("WECHAT_APPID")
        appsecret = os.getenv("WECHAT_APPSECRET")

        if not (appid and appsecret):
            logger.warning("⚠️ 微信凭证未配置，模拟发布")
            return {
                "publish_result": {"status": "simulated", "title": title, "reason": "凭证未配置"},
                "publish_success": True,
            }

        client = WeChatClient(appid, appsecret)

        # 生成封面图
        cover_media_id = None
        try:
            from image.generator import generate_cover_image
            import requests

            cover_url = generate_cover_image(title)
            resp = requests.get(cover_url, timeout=30)
            resp.raise_for_status()
            upload_result = client.upload_image(resp.content, "cover.jpg")
            cover_media_id = upload_result.get("media_id")
            logger.info(f"✅ 封面上传成功: {cover_media_id}")
        except Exception as e:
            logger.warning(f"⚠️ 封面图失败: {e}")

        if not cover_media_id and images:
            # 用正文第一张图作为封面
            try:
                first_img = images[0]
                if first_img.get("url") and not first_img.get("fallback", False):
                    import requests as req
                    resp = req.get(first_img["url"], timeout=30)
                    resp.raise_for_status()
                    upload_result = client.upload_image(resp.content, "fallback_cover.jpg")
                    cover_media_id = upload_result.get("media_id")
                    logger.info(f"✅ 使用正文图作为封面: {cover_media_id}")
            except Exception as e:
                logger.warning(f"⚠️ 备选封面也失败: {e}")

        # 处理标题长度（微信限制约64字节）
        import re
        title_bytes = len(title.encode('utf-8'))
        if title_bytes > 60:
            match = re.search(r'^.{10,30}?[：:,，。！？、]', title)
            if match:
                title = match.group(0)[:-1]
            while len(title.encode('utf-8')) > 60 and len(title) > 5:
                title = title[:-1]

        # 摘要
        digest = title[:54] if len(title.encode('utf-8')) > 54 else title

        article_data = {
            "title": title,
            "content": article_html,
            "thumb_media_id": cover_media_id or "",
            "author": config.get("publishing.author", "AI Writer"),
            "digest": digest,
            "content_source_url": "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }

        # 创建草稿
        logger.info(f"📝 创建草稿: {title}")
        media_id = client.add_draft([article_data])
        logger.info(f"✅ 草稿创建成功: {media_id}")

        # 尝试发布
        publish_result = {"media_id": media_id, "status": "draft"}
        try:
            publish_id = client.publish(media_id)
            publish_result["publish_id"] = publish_id
            publish_result["status"] = "published"
            logger.info(f"✅ 发布成功: {publish_id}")
        except Exception as e:
            publish_result["status"] = "draft_only"
            publish_result["message"] = "草稿已创建，请在公众号后台手动发布"
            logger.warning(f"⚠️ 自动发布失败（需认证服务号）: {e}")

        return {
            "publish_result": publish_result,
            "publish_success": True,
        }

    except Exception as e:
        logger.error(f"❌ Publisher 失败: {e}")
        return {
            "publish_result": {"error": str(e)},
            "publish_success": False,
            "errors": [{"node": "publisher", "error": str(e), "severity": "FATAL", "timestamp": ""}],
        }
