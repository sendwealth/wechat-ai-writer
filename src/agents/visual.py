"""
Agent: Visual - 图片规划 + 生成 + 微信上传
"""
import os
import requests
from langchain_core.runnables import RunnableConfig
from image.generator import generate_article_images, create_image_generator
from utils.config import config
from utils.logger import logger


def visual_node(state: dict, run_config=None) -> dict:
    """规划图片位置 → 生成 → 上传微信"""
    article = state.get("edited_article", state.get("draft_article", ""))
    topic = state.get("selected_title", state.get("topic_keyword", "科技"))
    highlights = state.get("key_data_points", [])

    provider = config.get_env("IMAGE_PROVIDER") or config.get("agents.visual.provider", "placeholder")
    num_images = int(config.get_env("NUM_IMAGES") or config.get("agents.visual.images_per_article", 2))

    logger.info(f"🖼️ Visual: 生成 {num_images} 张配图 (provider: {provider})")

    try:
        # 生成图片
        images = generate_article_images(
            topic=topic,
            highlights=highlights[:3],
            num_images=num_images,
            provider=provider,
        )

        # 如果是真实图片（非 placeholder），上传到微信
        if provider in ["cogview", "dalle3"]:
            appid = os.getenv("WECHAT_APPID")
            appsecret = os.getenv("WECHAT_APPSECRET")

            if appid and appsecret:
                try:
                    from wechat.client import WeChatClient
                    client = WeChatClient(appid, appsecret)

                    for img in images:
                        if not img.get("fallback", False) and img.get("url"):
                            try:
                                logger.info(f"   📥 下载并上传: {img['url'][:50]}...")
                                resp = requests.get(img["url"], timeout=30)
                                resp.raise_for_status()
                                wechat_url = client.upload_news_image(resp.content)
                                img["url"] = wechat_url
                                logger.info(f"   ✅ 已上传到微信")
                            except Exception as e:
                                logger.warning(f"   ⚠️ 上传失败: {e}")
                except Exception as e:
                    logger.warning(f"⚠️ WeChatClient 创建失败: {e}")

        success_count = sum(1 for img in images if not img.get("fallback", False))
        logger.info(f"✅ 图片生成完成: {success_count}/{len(images)} 成功")

        return {"article_images": images}

    except Exception as e:
        logger.error(f"❌ Visual 失败: {e}")
        return {
            "article_images": [],
            "errors": [{"node": "visual", "error": str(e), "severity": "DEGRADABLE", "timestamp": ""}],
        }
