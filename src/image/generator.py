"""
图片生成模块 - DALL-E 3 / CogView 集成
"""
import os
import base64
import requests
from typing import Dict, Any, List, Optional
from utils.logger import logger


class ImageGenerator:
    """图片生成器基类"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("IMAGE_API_KEY")
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成图片"""
        raise NotImplementedError


class DALLE3Generator(ImageGenerator):
    """DALL-E 3 图片生成器"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"))
        self.base_url = "https://api.openai.com/v1/images/generations"
    
    def generate(
        self,
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成图片
        
        Args:
            prompt: 图片描述
            model: 模型名称 (dall-e-3)
            size: 图片尺寸 (1024x1024, 1024x1792, 1792x1024)
            quality: 图片质量 (standard, hd)
            n: 生成数量 (1)
        
        Returns:
            {
                "url": "https://...",
                "revised_prompt": "优化后的提示词"
            }
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 未配置")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            if "data" in result and len(result["data"]) > 0:
                image_data = result["data"][0]
                return {
                    "url": image_data.get("url"),
                    "revised_prompt": image_data.get("revised_prompt", prompt)
                }
            else:
                raise Exception(f"生成失败: {result}")
        
        except Exception as e:
            logger.error(f"DALL-E 3 生成失败: {e}")
            raise


class CogViewGenerator(ImageGenerator):
    """智谱 CogView 图片生成器"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key or os.getenv("ZAI_API_KEY"))
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
    
    def generate(
        self,
        prompt: str,
        model: str = "cogview-3",
        size: str = "1024x1024",
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成图片（智谱 CogView）
        
        Args:
            prompt: 图片描述
            model: 模型名称 (cogview-3)
            size: 图片尺寸 (1024x1024)
        
        Returns:
            {
                "url": "https://..."
            }
        """
        if not self.api_key:
            raise ValueError("ZAI_API_KEY 未配置")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "prompt": prompt,
            "size": size
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            if "data" in result and len(result["data"]) > 0:
                image_data = result["data"][0]
                return {
                    "url": image_data.get("url"),
                    "revised_prompt": prompt
                }
            else:
                raise Exception(f"生成失败: {result}")
        
        except Exception as e:
            logger.error(f"CogView 生成失败: {e}")
            raise


class PlaceholderGenerator(ImageGenerator):
    """占位符生成器（测试用）"""
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成占位符图片"""
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        return {
            "url": f"https://via.placeholder.com/800x400?text={encoded_prompt}",
            "revised_prompt": prompt
        }


def create_image_generator(provider: str = None) -> ImageGenerator:
    """
    创建图片生成器
    
    Args:
        provider: 提供商 (dalle3, cogview, placeholder)
    
    Returns:
        ImageGenerator 实例
    """
    provider = provider or os.getenv("IMAGE_PROVIDER", "placeholder")
    
    if provider == "dalle3":
        return DALLE3Generator()
    elif provider == "cogview":
        return CogViewGenerator()
    elif provider == "placeholder":
        return PlaceholderGenerator()
    else:
        raise ValueError(f"不支持的图片生成提供商: {provider}")


def generate_article_images(
    topic: str,
    highlights: List[str],
    num_images: int = 2,
    provider: str = None
) -> List[Dict[str, Any]]:
    """
    为文章生成配图
    
    Args:
        topic: 文章主题
        highlights: 文章亮点
        num_images: 生成数量
        provider: 图片生成提供商
    
    Returns:
        [
            {
                "url": "https://...",
                "alt": "主题 配图 1",
                "position": 0
            }
        ]
    """
    generator = create_image_generator(provider)
    
    images = []
    for i in range(num_images):
        # 构建提示词
        if i == 0:
            # 第一张图：主题相关
            prompt = f"为科技文章'{topic}'生成配图，要求现代、科技感、高质量"
        else:
            # 后续图片：使用亮点
            highlight = highlights[i-1] if i-1 < len(highlights) else topic
            prompt = f"为科技文章亮点'{highlight}'生成配图，要求现代、科技感"
        
        try:
            logger.info(f"🎨 生成第 {i+1} 张图片: {prompt[:50]}...")
            result = generator.generate(prompt)
            
            images.append({
                "url": result["url"],
                "alt": f"{topic} 配图 {i+1}",
                "position": i,
                "prompt": result.get("revised_prompt", prompt)
            })
            
            logger.info(f"✅ 第 {i+1} 张图片生成成功")
        
        except Exception as e:
            logger.error(f"❌ 第 {i+1} 张图片生成失败: {e}")
            # 失败时使用占位符
            placeholder = PlaceholderGenerator()
            result = placeholder.generate(topic)
            images.append({
                "url": result["url"],
                "alt": f"{topic} 配图 {i+1}",
                "position": i,
                "prompt": prompt,
                "fallback": True
            })
    
    return images
