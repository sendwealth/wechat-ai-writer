"""
节点6: 插入图片 - 微信公众号富文本格式
"""
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from core.state import GlobalState
from utils.logger import logger


def add_images_node(state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
    """
    将图片插入文章（微信公众号富文本格式）
    
    Args:
        state: 全局状态
        config: 运行配置
    
    Returns:
        更新后的状态
    """
    logger.info("="*60)
    logger.info("🚀 节点6: 插入图片")
    logger.info("="*60)
    
    article = state.article
    images = state.article_images
    
    logger.info(f"📝 插入 {len(images)} 张图片")
    
    # 将 Markdown 转换为微信公众号富文本格式
    paragraphs = article.split('\n\n')
    
    html_parts = []
    image_idx = 0
    insert_positions = [
        max(1, len(paragraphs) // 3),
        max(2, len(paragraphs) * 2 // 3)
    ]
    
    for i, para in enumerate(paragraphs):
        # 处理标题
        if para.startswith('### '):
            title = para[4:]
            html_parts.append(f'''<h3 style="margin: 30px 0 15px 0; padding: 0; font-size: 18px; font-weight: bold; color: #333; line-height: 1.6;">{title}</h3>''')
        elif para.startswith('## '):
            title = para[3:]
            html_parts.append(f'''<h2 style="margin: 35px 0 18px 0; padding: 0; font-size: 20px; font-weight: bold; color: #333; line-height: 1.6;">{title}</h2>''')
        elif para.startswith('# '):
            title = para[2:]
            html_parts.append(f'''<h1 style="margin: 40px 0 20px 0; padding: 0; font-size: 24px; font-weight: bold; color: #333; line-height: 1.6;">{title}</h1>''')
        else:
            # 普通段落
            html_parts.append(f'''<p style="margin: 15px 0; padding: 0; font-size: 16px; line-height: 1.8; color: #333; text-align: justify; letter-spacing: 1px;">{para}</p>''')
        
        # 在指定位置插入图片
        if i in insert_positions and image_idx < len(images):
            img = images[image_idx]
            img_html = f'''<section style="margin: 25px 0; text-align: center;">
    <img src="{img["url"]}" alt="{img["alt"]}" style="width: 100%; max-width: 100%; height: auto; display: block; margin: 0 auto; border-radius: 4px;">
</section>'''
            html_parts.append(img_html)
            image_idx += 1
    
    # 如果还有剩余图片，添加到文章末尾
    while image_idx < len(images):
        img = images[image_idx]
        img_html = f'''<section style="margin: 25px 0; text-align: center;">
    <img src="{img["url"]}" alt="{img["alt"]}" style="width: 100%; max-width: 100%; height: auto; display: block; margin: 0 auto; border-radius: 4px;">
</section>'''
        html_parts.append(img_html)
        image_idx += 1
    
    # 组合完整的 HTML
    article_with_images = f'''<section style="padding: 20px 15px; font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei UI', 'Microsoft YaHei', Arial, sans-serif;">
{chr(10).join(html_parts)}
</section>'''
    
    logger.info(f"✅ 插入 {image_idx} 张图片")
    logger.info(f"   文章长度: {len(article_with_images)} 字符")
    
    logger.info("="*60)
    logger.info("✅ 节点6完成")
    logger.info("="*60)
    
    return {
        "article_with_images": article_with_images
    }
