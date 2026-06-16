"""
纯代码封面图生成器 — Pillow 本地生成，零 API 成本
绚烂紫色系：多段渐变 + 光晕 + 粒子星点 + 发光标题
微信公众号封面比例 900×383（2.35:1）
"""
import os
import math
import random
import textwrap
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from utils.logger import logger

# ═══ 配置 ═══
WIDTH, HEIGHT = 900, 383
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "covers"

# 统一紫色系 — 皇家紫→霓虹紫
PURPLE_THEME = [(25, 5, 60), (90, 20, 150), (200, 80, 255)]

# 字体路径（macOS 系统中文字体）
FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]


def _find_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """找到可用的中文字体"""
    bold_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    ]
    normal_paths = FONT_CANDIDATES
    paths = (bold_paths + normal_paths) if bold else normal_paths
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_gradient(img: Image.Image, theme: list):
    """绘制对角线多段渐变 — 比单色渐变更绚烂"""
    draw = ImageDraw.Draw(img)
    c1, c2, c3 = theme  # 深紫→中紫→亮紫

    for y in range(HEIGHT):
        ratio = y / HEIGHT
        if ratio < 0.5:
            # 上半部：c1 → c2
            r = ratio * 2
            cr = int(c1[0] + (c2[0] - c1[0]) * r)
            cg = int(c1[1] + (c2[1] - c1[1]) * r)
            cb = int(c1[2] + (c2[2] - c1[2]) * r)
        else:
            # 下半部：c2 → c3 混 c1（不要太亮，保持深色调）
            r = (ratio - 0.5) * 2
            cr = int(c2[0] + (c3[0] * 0.4 - c2[0]) * r)  # c3 降权混入
            cg = int(c2[1] + (c3[1] * 0.4 - c2[1]) * r)
            cb = int(c2[2] + (c3[2] * 0.5 - c2[2]) * r)
        draw.line([(0, y), (WIDTH, y)], fill=(cr, cg, cb))


def _draw_glow_circles(img: Image.Image, theme: list):
    """绘制发光圆 — 大尺寸 + 高斯模糊 = 光晕效果"""
    c3 = theme[2]  # 亮紫色
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)

    # 右上角大光晕
    draw.ellipse([WIDTH - 250, -120, WIDTH + 100, 180], fill=(*c3, 60))
    # 左下角光晕
    draw.ellipse([-150, HEIGHT - 160, 200, HEIGHT + 80], fill=(*c3, 45))
    # 中右小光晕
    draw.ellipse([WIDTH - 350, HEIGHT // 2 - 40, WIDTH - 200, HEIGHT // 2 + 100], fill=(*c3, 30))

    # 模糊产生光晕
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"))


def _draw_light_rays(img: Image.Image, theme: list):
    """绘制放射光线 — 从右上角发出"""
    c3 = theme[2]
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    cx, cy = WIDTH - 100, 50  # 光源点
    for angle_deg in range(-40, 60, 8):
        angle = math.radians(angle_deg - 90)
        length = 500
        x2 = cx + math.cos(angle) * length
        y2 = cy + math.sin(angle) * length
        # 宽度逐渐变窄的三角形光束
        draw.polygon(
            [(cx, cy), (x2 + 20, y2), (x2 - 20, y2)],
            fill=(*c3, 12),
        )

    overlay = overlay.filter(ImageFilter.GaussianBlur(25))
    return overlay


def _draw_particles(img: Image.Image, theme: list):
    """绘制星点粒子 — 随机散布的光点"""
    c3 = theme[2]
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    random.seed(42)  # 固定种子保持一致性
    for _ in range(60):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.choice([1, 1, 1, 2, 2, 3])
        alpha = random.randint(40, 160)
        draw.ellipse([x - size, y - size, x + size, y + size], fill=(255, 255, 255, alpha))

    # 几个大一点的紫色光点
    for _ in range(8):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.randint(3, 6)
        draw.ellipse([x - size, y - size, x + size, y + size], fill=(*c3, 100))

    return overlay


def _draw_title(img: Image.Image, title: str, theme: list):
    """绘制发光标题文字"""
    c3 = theme[2]
    max_width = WIDTH - 120

    # 自动缩小字号
    font_size = 48
    lines = []
    for fs in range(52, 30, -2):
        font = _find_font(fs, bold=True)
        lines = textwrap.wrap(title, width=max(6, int(max_width / (fs * 0.58))))
        if len(lines) <= 2:
            font_size = fs
            break

    font = _find_font(font_size, bold=True)
    if not lines:
        lines = [title]

    line_height = font_size + 10
    total_height = len(lines) * line_height
    y = (HEIGHT - total_height) // 2 - 5

    for line in lines:
        try:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
        except Exception:
            line_width = len(line) * font_size * 0.58

        x = (WIDTH - line_width) // 2

        # 文字发光层：大模糊 + 紫色
        glow_text = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_text)
        glow_draw.text((x, y), line, fill=(*c3, 180), font=font)
        glow_text = glow_text.filter(ImageFilter.GaussianBlur(6))
        img.paste(Image.alpha_composite(img.convert("RGBA"), glow_text).convert("RGB"))

        draw = ImageDraw.Draw(img)
        # 阴影
        draw.text((x + 2, y + 3), line, fill=(0, 0, 0, 160), font=font)
        # 主文字
        draw.text((x, y), line, fill=(255, 255, 255), font=font)
        y += line_height

    # 底部装饰：渐变线 + 光点
    draw = ImageDraw.Draw(img)
    line_y = HEIGHT - 28
    cx = WIDTH // 2
    # 短粗线
    draw.rectangle([cx - 40, line_y, cx + 40, line_y + 3], fill=(*c3, 200))
    # 两侧小光点
    for dx in [-55, 55]:
        draw.ellipse([cx + dx - 2, line_y, cx + dx + 4, line_y + 4], fill=(*c3, 220))
    # 更远的小点
    for dx in [-75, 75]:
        draw.ellipse([cx + dx - 1, line_y + 1, cx + dx + 2, line_y + 3], fill=(*c3, 120))


def generate_cover(
    title: str,
    category: str = "",
    output_path: Optional[str] = None,
) -> str:
    """
    生成绚烂紫色系封面图并保存为 PNG。
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    theme = PURPLE_THEME

    # 创建画布
    img = Image.new("RGB", (WIDTH, HEIGHT), theme[0])

    # 1. 多段渐变背景
    _draw_gradient(img, theme)

    # 2. 发光圆光晕
    _draw_glow_circles(img, theme)

    # 3. 放射光线
    rays_overlay = _draw_light_rays(img, theme)
    img = Image.alpha_composite(
        img.convert("RGBA"), rays_overlay
    ).convert("RGB")

    # 4. 粒子星点
    particles = _draw_particles(img, theme)
    img = Image.alpha_composite(
        img.convert("RGBA"), particles
    ).convert("RGB")

    # 5. 发光标题
    _draw_title(img, title, theme)

    # 6. 整体微调：轻微暗角增强中心聚焦
    vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    vignette_draw = ImageDraw.Draw(vignette)
    for i in range(30):
        alpha = int(i * 1.5)
        vignette_draw.rectangle(
            [i, i, WIDTH - i, HEIGHT - i],
            outline=(0, 0, 0, alpha),
        )
    vignette = vignette.filter(ImageFilter.GaussianBlur(15))
    img = Image.alpha_composite(
        img.convert("RGBA"), vignette
    ).convert("RGB")

    # 保存
    if output_path is None:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in title[:20])
        output_path = str(OUTPUT_DIR / f"cover_{safe}.png")

    img.save(output_path, "PNG", optimize=True)
    logger.info(f"🖼️ 封面图已生成: {output_path} ({os.path.getsize(output_path) // 1024}KB)")

    return output_path
