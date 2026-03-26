"""
微信公众号客户端 - 自动获取 Access Token
"""
import os
import requests
import base64
from typing import Dict, Any, Optional
from utils.logger import logger


class WeChatClient:
    """微信公众号客户端 - 自动管理 Access Token"""
    
    def __init__(self, appid: Optional[str] = None, appsecret: Optional[str] = None, access_token: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            appid: AppID（可选，从环境变量读取）
            appsecret: AppSecret（可选，从环境变量读取）
            access_token: Access Token（可选，优先级最低）
        """
        # 优先级：1. 参数传入 > 2. 环境变量
        self.appid = appid or os.getenv("WECHAT_APPID")
        self.appsecret = appsecret or os.getenv("WECHAT_APPSECRET")
        self.access_token = access_token or os.getenv("WECHAT_ACCESS_TOKEN")
        
        # 验证配置
        if not self.access_token and not (self.appid and self.appsecret):
            raise ValueError("必须配置 WECHAT_ACCESS_TOKEN 或 (WECHAT_APPID + WECHAT_APPSECRET)")
        
        # 缓存 token 和过期时间
        self._token_cache = {
            "token": None,
            "expires_at": 0
        }
    
    def _get_token_from_api(self) -> str:
        """通过 AppID + AppSecret 获取 access_token（绕过 IP 限制）"""
        if not self.appid or not self.appsecret:
            raise ValueError("AppID 和 AppSecret 未配置")
        
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.appsecret}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "errcode" in data:
                raise Exception(f"获取 access_token 失败: {data.get('errmsg')}")
            
            # 缓存 token
            self._token_cache["token"] = data["access_token"]
            self._token_cache["expires_at"] = int(time.time()) + data["expires_in"] - 300  # 提前5分钟过期
            
            logger.info(f"成功获取 access_token，有效期: {data['expires_in']} 秒")
            return data["access_token"]
            
        except Exception as e:
            logger.error(f"获取 access_token 失败: {e}")
            raise
    
    def get_valid_token(self) -> str:
        """
        获取有效的 access_token
        
        优先级：
        1. 如果有缓存的 token 且未过期，        2. 如果配置了 AppID + AppSecret，自动获取新 token
        3. 使用静态配置的 access_token
        """
        # 1. 检查缓存
        if self._token_cache["token"] and time.time() < self._token_cache["expires_at"]:
            return self._token_cache["token"]
        
        # 2. 尝试通过 API 获取
        if self.appid and self.appsecret:
            try:
                return self._get_token_from_api()
            except Exception as e:
                logger.warning(f"通过 API 获取 token 失败: {e}，使用静态配置")
        
        # 3. 使用静态配置
        if not self.access_token:
            raise ValueError("无法获取有效的 access_token")
        
        return self.access_token
    
    def upload_image(self, image_data: bytes, filename: str = "image.jpg") -> Dict[str, Any]:
        """
        上传永久图片
        
        Args:
            image_data: 图片二进制数据
            filename: 文件名
        
        Returns:
            {"media_id": "xxx", "url": "xxx"}
        """
        token = self.get_valid_token()
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
        
        files = {"media": (filename, image_data)}
        
        try:
            response = requests.post(url, files=files, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode", 0) != 0:
                raise Exception(f"上传图片失败: {data}")
            
            logger.info(f"上传图片成功: {data.get('media_id')}")
            return {
                "media_id": data.get("media_id"),
                "url": data.get("url")
            }
        except Exception as e:
            logger.error(f"上传图片异常: {e}")
            raise
    
    def upload_news_image(self, image_data: bytes, filename: str = "image.jpg") -> str:
        """
        上传图文消息内的图片
        
        Args:
            image_data: 图片二进制数据
            filename: 文件名
        
        Returns:
            图片 URL
        """
        token = self.get_valid_token()
        url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
        
        files = {"media": (filename, image_data)}
        
        try:
            response = requests.post(url, files=files, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode", 0) != 0:
                raise Exception(f"上传图文图片失败: {data}")
            
            logger.info(f"上传图文图片成功: {data.get('url')}")
            return data.get("url")
        except Exception as e:
            logger.error(f"上传图文图片异常: {e}")
            raise
    
    def add_draft(self, articles: list) -> str:
        """
        新建草稿
        
        Args:
            articles: 文章列表
        
        Returns:
            media_id
        """
        token = self.get_valid_token()
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
        
        payload = {"articles": articles}
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode", 0) != 0:
                raise Exception(f"创建草稿失败: {data}")
            
            media_id = data.get("media_id")
            logger.info(f"创建草稿成功: {media_id}")
            return media_id
        except Exception as e:
            logger.error(f"创建草稿异常: {e}")
            raise
    
    def publish(self, media_id: str) -> str:
        """
        发布草稿
        
        Args:
            media_id: 草稿 media_id
        
        Returns:
            publish_id
        """
        token = self.get_valid_token()
        url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={token}"
        
        payload = {"media_id": media_id}
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode", 0) != 0:
                raise Exception(f"发布失败: {data}")
            
            publish_id = data.get("publish_id")
            logger.info(f"发布成功: {publish_id}")
            return publish_id
        except Exception as e:
            logger.error(f"发布异常: {e}")
            raise
    
    def get_publish_status(self, publish_id: str) -> Dict[str, Any]:
        """
        查询发布状态
        
        Args:
            publish_id: 发布 ID
        
        Returns:
            发布状态
        """
        token = self.get_valid_token()
        url = f"https://api.weixin.qq.com/cgi-bin/freepublish/get?access_token={token}"
        
        payload = {"publish_id": publish_id}
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode", 0) != 0:
                raise Exception(f"查询发布状态失败: {data}")
            
            return data
        except Exception as e:
            logger.error(f"查询发布状态异常: {e}")
            raise
