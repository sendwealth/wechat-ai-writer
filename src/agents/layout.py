"""
Agent: Layout - 微信公众号 HTML 排版
"""
from langchain_core.runnables import RunnableConfig
from utils.logger import logger


def _render_paragraph(text: str) -> str:
    """渲染单个段落为微信 HTML"""
    text = text.strip()
    if not text:
        return ""

    # 处理标题行
    if text.startswith('# ') and not text.startswith('## '):
        title = text[2:].strip()
        return f'<h2 style="margin: 35px 0 18px; padding: 0; font-size: 20px; font-weight: bold; color: #1a1a1a; line-height: 1.6;">{title}</h2>'
    if text.startswith('## '):
        title = text[3:].strip()
        return f'<h3 style="margin: 30px 0 15px; padding: 0; font-size: 18px; font-weight: bold; color: #1a1a1a; line-height: 1.6;">{title}</h3>'
    if text.startswith('### '):
        title = text[4:].strip()
        return f'<h4 style="margin: 25px 0 12px; padding: 0; font-size: 16px; font-weight: bold; color: #333; line-height: 1.6;">{title}</h4>'

    # 处理列表项
    if text.startswith(('• ', '- ', '· ')):
        content = text[2:].strip()
        return f'<p style="margin: 8px 0; padding-left: 15px; font-size: 15px; line-height: 1.75; color: #333; letter-spacing: 0.5px;">• {content}</p>'

    # 检查是否为编号列表 (①②③ 或 1. 2. 3.)
    import re
    if re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', text):
        return f'<p style="margin: 8px 0; padding-left: 15px; font-size: 15px; line-height: 1.75; color: #333; letter-spacing: 0.5px;">{text}</p>'

    # 普通段落
    return f'<p style="margin: 15px 0; padding: 0; font-size: 15px; line-height: 1.75; color: #333; text-align: justify; letter-spacing: 0.5px;">{text}</p>'


def _render_image(img: dict) -> str:
    """渲染图片为微信 HTML"""
    url = img.get("url", "")
    alt = img.get("alt", "")
    return f'''<section style="margin: 20px 0; text-align: center;">
    <img src="{url}" alt="{alt}" style="width: 100%; max-width: 100%; height: auto; display: block; margin: 0 auto; border-radius: 6px;">
</section>'''


def layout_node(state: dict, run_config=None) -> dict:
    """将文章 + 图片渲染为微信公众号 HTML"""
    article = state.get("edited_article", state.get("draft_article", ""))
    images = state.get("article_images", [])

    logger.info(f"🎨 Layout: 排版文章 ({len(article)} 字符, {len(images)} 张图片)")

    if not article:
        return {"article_html": ""}

    # 分段
    paragraphs = article.split('\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    html_parts = []
    image_idx = 0

    # 计算图片插入位置（均匀分布）
    total_paras = len(paragraphs)
    insert_positions = set()
    if images and total_paras > 3:
        for i in range(len(images)):
            pos = int(total_paras * (i + 1) / (len(images) + 1))
            insert_positions.add(pos)

    for i, para in enumerate(paragraphs):
        # 检查是否为图片占位符
        if para.startswith('[IMG:'):
            if image_idx < len(images):
                html_parts.append(_render_image(images[image_idx]))
                image_idx += 1
            continue

        html_parts.append(_render_paragraph(para))

        # 在指定位置插入图片
        if i in insert_positions and image_idx < len(images):
            html_parts.append(_render_image(images[image_idx]))
            image_idx += 1

    # 剩余图片追加到末尾
    while image_idx < len(images):
        html_parts.append(_render_image(images[image_idx]))
        image_idx += 1

    # 组合完整 HTML
    article_html = f'''<section style="padding: 20px 15px; font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei UI', 'Microsoft YaHei', Arial, sans-serif;">
{chr(10).join(html_parts)}
</section>'''

    logger.info(f"✅ 排版完成: {len(article_html)} 字符, 插入 {image_idx} 张图片")

    return {"article_html": article_html}
