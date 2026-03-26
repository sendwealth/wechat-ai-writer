#!/usr/bin/env python3
"""
创建默认封面图片
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_default_cover():
    """创建一个简单的默认封面图片"""
    # 创建 900x500 的图片（微信公众号推荐尺寸）
    width, height = 900, 500
    img = Image.new('RGB', (width, height), color='#2563eb')  # 蓝色背景
    
    draw = ImageDraw.Draw(img)
    
    # 添加标题文字
    title = "AI科技前沿"
    subtitle = "WeChat AI Writer"
    
    # 使用默认字体（如果系统有中文字体可以指定）
    try:
        # 尝试使用系统字体
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except:
        # 使用默认字体
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # 计算文字位置（居中）
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    title_y = height // 2 - 80
    
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    subtitle_y = height // 2 + 40
    
    # 绘制文字（白色）
    draw.text((title_x, title_y), title, fill='white', font=title_font)
    draw.text((subtitle_x, subtitle_y), subtitle, fill='#e0e7ff', font=subtitle_font)
    
    # 添加装饰线条
    draw.rectangle([100, height//2 - 100, width - 100, height//2 - 95], fill='white')
    draw.rectangle([100, height//2 + 120, width - 100, height//2 + 125], fill='white')
    
    # 保存图片
    output_path = "wechat-ai-writer/assets/default_cover.jpg"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, 'JPEG', quality=95)
    
    print(f"✅ 封面图片已创建: {output_path}")
    return output_path

if __name__ == "__main__":
    create_cover_path = create_default_cover()
    print(f"路径: {create_cover_path}")
