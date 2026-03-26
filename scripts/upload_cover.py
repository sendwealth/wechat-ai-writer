#!/usr/bin/env python3
"""
上传封面图片到微信公众号
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, '/root/.openclaw/workspace/wechat-ai-writer/src')

from wechat.client import WeChatClient
from utils.logger import logger

def upload_cover():
    """上传封面图片并获取 media_id"""
    # 读取配置
    from dotenv import load_dotenv
    load_dotenv('/root/.openclaw/workspace/wechat-ai-writer/.env')
    
    appid = os.getenv("WECHAT_APPID")
    appsecret = os.getenv("WECHAT_APPSECRET")
    
    if not appid or not appsecret:
        logger.error("❌ 未配置 WECHAT_APPID 或 WECHAT_APPSECRET")
        return None
    
    # 创建客户端
    client = WeChatClient(appid=appid, appsecret=appsecret)
    
    # 读取封面图片
    cover_path = "/root/.openclaw/workspace/wechat-ai-writer/assets/default_cover.jpg"
    
    if not os.path.exists(cover_path):
        logger.error(f"❌ 封面图片不存在: {cover_path}")
        return None
    
    with open(cover_path, 'rb') as f:
        image_data = f.read()
    
    logger.info(f"📤 上传封面图片: {cover_path}")
    logger.info(f"   图片大小: {len(image_data)} bytes")
    
    try:
        # 上传永久素材
        result = client.upload_image(image_data, "default_cover.jpg")
        
        media_id = result.get("media_id")
        url = result.get("url")
        
        logger.info(f"✅ 上传成功!")
        logger.info(f"   media_id: {media_id}")
        logger.info(f"   url: {url}")
        
        # 保存到文件
        with open("/root/.openclaw/workspace/wechat-ai-writer/.cover_media_id", 'w') as f:
            f.write(media_id)
        
        logger.info(f"💾 media_id 已保存到: .cover_media_id")
        
        return media_id
        
    except Exception as e:
        logger.error(f"❌ 上传失败: {e}")
        return None

if __name__ == "__main__":
    media_id = upload_cover()
    if media_id:
        print(f"\n✅ 封面 media_id: {media_id}")
    else:
        print("\n❌ 上传失败")
