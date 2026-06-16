"""
Agent: Layout - 微信公众号 HTML 排版（花哨版）
自动识别标题/正文/列表/引用/金句，渲染视觉层次丰富的排版。
"""
import re
from utils.logger import logger

# ═══ 配色方案 ═══
C_PRIMARY = "#2c7be5"    # 主色（科技蓝）
C_ACCENT  = "#ff6b35"    # 强调色（活力橙）
C_DARK    = "#1a1a1a"    # 正文深色
C_BODY    = "#3f3f3f"    # 正文灰
C_MUTED   = "#888"       # 辅助灰
C_BG_HL   = "#fff8e1"    # 金句背景（暖黄）
C_BG_QUO  = "#f0f5ff"    # 引用背景（淡蓝）
C_BG_END  = "#f8f9fa"    # 结尾背景（浅灰）
C_BORDER  = "#e8e8e8"    # 边框灰
C_GREEN   = "#00b894"    # 数据绿
C_DIV     = "#d0d0d0"    # 分割线


def _is_section_title(text: str, idx: int, prev_blank: bool, next_blank: bool) -> bool:
    """
    启发式判断是否为小标题：
    - 不是第一段（第一段是文章大标题）
    - 独立一行（前后空行）
    - 较短（≤45字）
    - 不以句号/感叹号/问号结尾（允许逗号和冒号）
    - 不是图片占位符
    """
    if not text or len(text) > 45:
        return False
    if idx == 0:  # 第一段是文章标题，不算小标题
        return False
    if text.startswith('[IMG:'):
        return False
    # 句号/感叹号/问号结尾 → 是正文不是标题
    if re.search(r'[。！？]$', text):
        return False
    # 以问号开头或包含问号 → 大概率是互动提问不是标题
    if '?' in text or '？' in text:
        return False
    # 太短的不像标题（除非有数字编号）
    if len(text) <= 3 and not re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', text):
        return False
    # 检测是否包含连续句子（2个以上句号/感叹号 → 不是标题）
    if len(re.findall(r'[。！？]', text)) >= 1:
        return False
    # 必须前后都有空行（标题是独立的）
    return prev_blank and next_blank


def _render_title(text: str) -> str:
    """渲染小标题：左侧色条 + 文字 + 底部渐变线"""
    return (
        f'<section style="margin: 32px 0 18px; display: flex; align-items: center;">'
        f'<span style="display: inline-block; width: 4px; height: 22px; '
        f'background: {C_PRIMARY}; border-radius: 2px; margin-right: 12px; flex-shrink: 0;"></span>'
        f'<span style="font-size: 19px; font-weight: bold; color: {C_DARK}; line-height: 1.4;">{text}</span>'
        f'</section>'
    )


def _render_numbered_title(text: str) -> str:
    """渲染编号小标题（如「场景一：xxx」）"""
    return (
        f'<section style="margin: 32px 0 18px; padding: 12px 16px; '
        f'background: linear-gradient(135deg, #f0f5ff 0%, #ffffff 100%); '
        f'border-left: 4px solid {C_PRIMARY}; border-radius: 0 8px 8px 0;">'
        f'<span style="font-size: 19px; font-weight: bold; color: {C_DARK}; line-height: 1.4;">{text}</span>'
        f'</section>'
    )


def _render_highlight_box(text: str) -> str:
    """
    渲染【...】金句框：暖色背景 + 左侧色条 + 引号装饰
    支持【整段】和【句中嵌】两种情况
    """
    return (
        f'<section style="margin: 20px 0; padding: 16px 20px; '
        f'background: {C_BG_HL}; border-left: 4px solid {C_ACCENT}; '
        f'border-radius: 0 8px 8px 0;">'
        f'<span style="font-size: 22px; color: {C_ACCENT}; font-weight: bold; line-height: 1;">❝</span>'
        f'<span style="font-size: 16px; color: {C_DARK}; line-height: 1.75; font-weight: 500;">{text}</span>'
        f'<span style="font-size: 22px; color: {C_ACCENT}; font-weight: bold; line-height: 1;">❞</span>'
        f'</section>'
    )


def _render_inline_highlight(text: str) -> str:
    """句中【xxx】→ 高亮 span"""
    return f'<span style="color: {C_ACCENT}; font-weight: bold;">{text}</span>'


def _render_quote(text: str) -> str:
    """渲染引用/数据来源：淡蓝背景 + 左竖线"""
    return (
        f'<section style="margin: 16px 0; padding: 12px 16px; '
        f'background: {C_BG_QUO}; border-left: 3px solid {C_PRIMARY}; '
        f'border-radius: 0 6px 6px 0;">'
        f'<p style="margin: 0; font-size: 16px; color: #555; line-height: 1.7; '
        f'font-style: italic;">{text}</p>'
        f'</section>'
    )


def _render_list_item(text: str) -> str:
    """渲染列表项：彩色圆点"""
    content = re.sub(r'^[•·\-]\s*', '', text)
    content = _process_inline(content)
    return (
        f'<section style="margin: 8px 0; padding-left: 8px; display: flex; align-items: flex-start;">'
        f'<span style="display: inline-block; width: 6px; height: 6px; '
        f'background: {C_PRIMARY}; border-radius: 50%; margin: 9px 10px 0 0; flex-shrink: 0;"></span>'
        f'<span style="font-size: 16px; color: {C_BODY}; line-height: 1.75; flex: 1;">{content}</span>'
        f'</section>'
    )


def _render_numbered_item(text: str) -> str:
    """渲染编号列表（①②③）：圆圈样式"""
    match = re.match(r'^([①②③④⑤⑥⑦⑧⑨⑩])\s*(.*)', text)
    if match:
        num, content = match.group(1), match.group(2)
    else:
        match2 = re.match(r'^(\d+)[.、]\s*(.*)', text)
        if match2:
            num, content = match2.group(1), match2.group(2)
        else:
            num, content = "•", text

    content = _process_inline(content)
    return (
        f'<section style="margin: 8px 0; padding-left: 4px; display: flex; align-items: flex-start;">'
        f'<span style="display: inline-block; min-width: 22px; height: 22px; line-height: 22px; '
        f'text-align: center; background: {C_PRIMARY}; color: #fff; '
        f'border-radius: 50%; font-size: 13px; font-weight: bold; margin: 3px 10px 0 0; '
        f'flex-shrink: 0;">{num}</span>'
        f'<span style="font-size: 16px; color: {C_BODY}; line-height: 1.75; flex: 1;">{content}</span>'
        f'</section>'
    )


def _render_divider() -> str:
    """章节分割线：居中三点装饰"""
    return (
        f'<section style="text-align: center; margin: 28px 0; color: {C_DIV}; '
        f'font-size: 16px; letter-spacing: 8px;">· · ·</section>'
    )


def _render_paragraph(text: str) -> str:
    """渲染普通段落"""
    text = _process_inline(text)
    return (
        f'<p style="margin: 14px 0; padding: 0; font-size: 16px; line-height: 1.8; '
        f'color: {C_BODY}; letter-spacing: 0.3px;">{text}</p>'
    )


def _render_leading_paragraph(text: str) -> str:
    """渲染开篇段落：加重字号 + 深色"""
    text = _process_inline(text)
    return (
        f'<p style="margin: 16px 0; padding: 0; font-size: 17px; line-height: 1.85; '
        f'color: {C_DARK}; letter-spacing: 0.3px; font-weight: 500;">{text}</p>'
    )


def _render_closing_box(text: str) -> str:
    """渲染结尾互动引导框"""
    text = _process_inline(text)
    return (
        f'<section style="margin: 28px 0 10px; padding: 18px 20px; '
        f'background: {C_BG_END}; border-radius: 12px; '
        f'border: 1px solid {C_BORDER};">'
        f'<p style="margin: 0; font-size: 15px; color: {C_MUTED}; line-height: 1.7;">💬 {text}</p>'
        f'</section>'
    )


def _process_inline(text: str) -> str:
    """
    处理行内格式：
    - 【xxx】→ 高亮 span
    - 「xxx」→ 保持（微信兼容）
    - 关键数字 → 数据色强调
    """
    # 【】高亮
    text = re.sub(
        r'【(.+?)】',
        lambda m: _render_inline_highlight(m.group(1)),
        text
    )

    # 数字+百分比/倍数 → 数据色（如 3倍、70%、40%）
    text = re.sub(
        r'(?<![\w>])(\d+(?:\.\d+)?(?:%|倍|万|亿|个|小时|天|分钟|秒))(?![\w<])',
        lambda m: f'<span style="color: {C_GREEN}; font-weight: bold;">{m.group(1)}</span>',
        text
    )

    return text


def _render_article_title(text: str) -> str:
    """渲染文章大标题（第一行）：居中 + 装饰线"""
    return (
        f'<section style="margin: 0 0 24px; text-align: center; padding: 20px 0;">'
        f'<p style="margin: 0 0 12px; font-size: 24px; font-weight: bold; '
        f'color: {C_DARK}; line-height: 1.4; letter-spacing: 1px;">{text}</p>'
        f'<span style="display: inline-block; width: 40px; height: 3px; '
        f'background: {C_PRIMARY}; border-radius: 2px;"></span>'
        f'</section>'
    )


def _classify_and_render(para: str, idx: int, total: int, prev_blank: bool, next_blank: bool) -> str:
    """对段落分类并调用对应渲染函数"""
    stripped = para.strip()

    # 图片占位符跳过
    if stripped.startswith('[IMG:'):
        return ""

    # 第一段 → 文章大标题
    if idx == 0:
        return _render_article_title(stripped)

    # 【】独占一行 → 金句框
    if re.match(r'^【[^】]+】$', stripped) and len(stripped) < 120:
        inner = stripped[1:-1]
        return _render_highlight_box(inner)

    # 引用/数据来源行（以「据」、「根据」等开头）
    quote_patterns = [
        r'^据[《""].+?[》""]',
        r'^根据.+?[《""].+?[》""]',
        r'^数据显示',
        r'^统计显示',
    ]
    for pat in quote_patterns:
        if re.match(pat, stripped) and len(stripped) < 80:
            return _render_quote(stripped)

    # 列表项
    if re.match(r'^[•·\-]\s+', stripped):
        return _render_list_item(stripped)

    # 编号列表
    if re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]\s*', stripped):
        return _render_numbered_item(stripped)
    if re.match(r'^\d+[.、]\s+', stripped) and len(stripped) < 200:
        return _render_numbered_item(stripped)

    # 编号小标题（「场景一：」「第一，」等）
    if re.match(r'^(场景[一二三四五六]|第[一二三四五六七八九十]+[：:])', stripped) and next_blank:
        return _render_numbered_title(stripped)

    # 小标题检测
    if _is_section_title(stripped, idx, prev_blank, next_blank):
        return _render_title(stripped)

    # 最后一段 → 互动引导框（如果包含问号或引导语）
    is_last = (idx >= total - 2)
    closing_hints = ['？', '?', '评论', '留言', '分享', '你觉得', '你怎么看', '欢迎']
    if is_last and any(h in stripped for h in closing_hints) and len(stripped) < 150:
        return _render_closing_box(stripped)

    # 开篇段落（第2-3段，紧跟大标题）
    if idx <= 2:
        return _render_leading_paragraph(stripped)

    # 普通段落
    return _render_paragraph(stripped)


def layout_node(state: dict, run_config=None) -> dict:
    """将文章渲染为微信公众号 HTML（花哨版）"""
    article = state.get("edited_article", state.get("draft_article", ""))

    logger.info(f"🎨 Layout: 排版文章 ({len(article)} 字符)")

    if not article:
        return {"article_html": ""}

    # 按双换行分段，保留单换行信息
    raw_blocks = re.split(r'\n\n+', article)
    blocks = []
    for block in raw_blocks:
        block = block.strip()
        if block:
            # 单换行连接为一段
            block = re.sub(r'\n', ' ', block)
            blocks.append(block)

    total = len(blocks)
    html_parts = []

    for i, para in enumerate(blocks):
        prev_blank = (i > 0)  # 前面有段落 = 前面有空行
        next_blank = (i < total - 1)  # 后面还有段落

        rendered = _classify_and_render(para, i, total, prev_blank, next_blank)
        if rendered:
            html_parts.append(rendered)

            # 在标题后不加分隔线（标题自带间距）
            # 在段落和小标题之间加分隔线
            if next_blank and i < total - 2:
                next_para = blocks[i + 1] if i + 1 < total else ""
                # 如果下一段是标题，当前段不是标题 → 加分隔线
                if _is_section_title(next_para.strip(), i+1, True, True) and not _is_section_title(para.strip(), i, prev_blank, True):
                    # 只在「正文→标题」过渡时加，不在「标题→正文」时加
                    html_parts.append(_render_divider())

    # 组装最终 HTML
    article_html = f'''<section style="padding: 16px 12px; font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei UI', 'Microsoft YaHei', Arial, sans-serif; max-width: 100%; overflow-wrap: break-word; word-break: break-all;">

{chr(10).join(html_parts)}

</section>'''

    logger.info(f"✅ 排版完成: {len(article_html)} 字符, {total} 段")

    return {"article_html": article_html}
