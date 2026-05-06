"""
Agent: Layout - 微信公众号 HTML 排版
"""
import re
from utils.logger import logger


def _render_paragraph(text: str) -> str:
    """渲染单个段落为微信 HTML"""
    text = text.strip()
    if not text:
        return ""

    # 处理标题行
    if text.startswith('# ') and not text.startswith('## '):
        title = text[2:].strip()
        return f'<h2 style="margin: 35px 0 18px; padding: 0; font-size: 22px; font-weight: bold; color: #1a1a1a; line-height: 1.6;">{title}</h2>'
    if text.startswith('## '):
        title = text[3:].strip()
        return f'<h3 style="margin: 30px 0 15px; padding: 0; font-size: 20px; font-weight: bold; color: #1a1a1a; line-height: 1.6;">{title}</h3>'
    if text.startswith('### '):
        title = text[4:].strip()
        return f'<h4 style="margin: 25px 0 12px; padding: 0; font-size: 18px; font-weight: bold; color: #333; line-height: 1.6;">{title}</h4>'

    # 处理列表项
    if text.startswith(('• ', '- ', '· ')):
        content = text[2:].strip()
        return f'<p style="margin: 8px 0; padding-left: 15px; font-size: 17px; line-height: 1.75; color: #333; letter-spacing: 0.5px;">• {content}</p>'

    # 检查是否为编号列表 (①②③ 或 1. 2. 3.)
    if re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', text):
        return f'<p style="margin: 8px 0; padding-left: 15px; font-size: 17px; line-height: 1.75; color: #333; letter-spacing: 0.5px;">{text}</p>'

    # 普通段落
    return f'<p style="margin: 15px 0; padding: 0; font-size: 17px; line-height: 1.75; color: #333; text-align: justify; letter-spacing: 0.5px;">{text}</p>'


def layout_node(state: dict, run_config=None) -> dict:
    """将文章渲染为微信公众号 HTML"""
    article = state.get("edited_article", state.get("draft_article", ""))

    logger.info(f"🎨 Layout: 排版文章 ({len(article)} 字符)")

    if not article:
        return {"article_html": ""}

    paragraphs = [p.strip() for p in article.split('\n') if p.strip()]

    html_parts = []
    for para in paragraphs:
        # 跳过图片占位符
        if para.startswith('[IMG:'):
            continue
        html_parts.append(_render_paragraph(para))

    article_html = f'''<section style="padding: 20px 15px; font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei UI', 'Microsoft YaHei', Arial, sans-serif;">
{chr(10).join(html_parts)}
</section>'''

    logger.info(f"✅ 排版完成: {len(article_html)} 字符")

    return {"article_html": article_html}
