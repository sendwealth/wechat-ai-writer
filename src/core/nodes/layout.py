"""
节点6: 插入图片
"""
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from core.state import GlobalState
from utils.logger import logger


def add_images_node(state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
    """
    将图片插入文章
    
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
    
    # 在文章中插入图片
    paragraphs = article.split('\n\n')
    
    # 在 1/3 和 2/3 位置插入图片
    result_paragraphs = []
    insert_positions = [
        max(1, len(paragraphs) // 3),
        max(2, len(paragraphs) * 2 // 3)
    ]
    
    image_idx = 0
    for i, para in enumerate(paragraphs):
        result_paragraphs.append(para)
        
        if i in insert_positions and image_idx < len(images):
            img = images[image_idx]
            img_html = f'<img src="{img["url"]}" alt="{img["alt"]}" style="width:100%;margin:20px 0;">'
            result_paragraphs.append(img_html)
            image_idx += 1
    
    article_with_images = '\n\n'.join(result_paragraphs)
    
    logger.info(f"✅ 插入 {image_idx} 张图片")
    logger.info(f"   文章长度: {len(article_with_images)} 字符")
    
    logger.info("="*60)
    logger.info("✅ 节点6完成")
    logger.info("="*60)
    
    return {
        "article_with_images": article_with_images
    }
