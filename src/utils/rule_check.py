"""
规则预检层 — 在 LLM 评分之前做硬规则检查
零成本拦截低质量输出，生成结构化修正指令
"""
import re
from collections import Counter

# ═══ AI味关键词黑名单 ═══
# 来源：critic.md 29项检测 + writer.md 禁令 + humanizer 方法论
AI_FLAVOR_KEYWORDS = {
    # 意义夸大
    "标志着": 0.3, "具有里程碑意义": 0.3, "深远影响": 0.3, "不可或缺": 0.3,
    "开创了新纪元": 0.3, "开创了": 0.3,
    # 推广腔调
    "备受瞩目": 0.3, "令人瞩目": 0.3, "引发广泛关注": 0.3,
    "赋能": 0.3, "全方位": 0.2, "一站式": 0.2,
    "颠覆": 0.2, "重塑": 0.2, "打造了": 0.2,
    # 「着」式虚假深度
    "体现着": 0.2, "彰显着": 0.2, "反映着": 0.2, "意味着": 0.2, "蕴含着": 0.2,
    # AI高频中文词
    "此外": 0.2, "至关": 0.2, "深入探讨": 0.2, "凸显": 0.2,
    "交织": 0.2, "错综复杂": 0.2, "画卷": 0.2, "生动展现": 0.2,
    "蓬勃": 0.2, "涌现": 0.2, "助力": 0.2,
    # 元语言
    "让我们深入": 0.2, "接下来我们来看": 0.2, "让我们拭目以待": 0.2,
    "未来可期": 0.2, "前景广阔": 0.2, "未来充满无限可能": 0.2,
    "综上所述": 0.2, "总而言之": 0.2, "归根结底": 0.2,
    "值得注意的是": 0.2, "毋庸置疑": 0.2,
    # 被动回避
    "被广泛应用于": 0.2, "被誉为": 0.2,
    # ══ v2 新增：从实际输出中发现的漏网 AI 味 ══
    # 夸大升级/性能
    "断层式": 0.3, "跨时代": 0.3, "性能狂飙": 0.3, "刷新了历史": 0.3,
    "历史性": 0.2, "史诗级": 0.3, "降维打击": 0.3, "王炸": 0.2,
    # AI 路标词（当小标题用）
    "现象引入": 0.3, "总结升华": 0.3, "核心观点": 0.2, "深度解析": 0.2,
    # 过度修辞
    "彻底重构": 0.3, "彻底颠覆": 0.3, "彻底改变": 0.2, "重塑一切": 0.3,
    "本质上": 0.2, "核心在于": 0.2, "关键在于": 0.2,
    # AI 式总结开头
    "在这个数字化": 0.3, "在当今": 0.2,
    "日新月异": 0.2, "如火如荼": 0.2, "方兴未艾": 0.2,
}

# 正则模式：检测更灵活的匹配
AI_FLAVOR_PATTERNS = [
    (r"不仅.{1,10}而且.{1,10}还", 0.2, "「不仅…而且…还」三段递进"),
    (r"从.{1,8}到.{1,8}，从.{1,8}到", 0.2, "「从X到Y，从A到B」虚假范围"),
    (r"首先[，,].{1,30}其次[，,].{1,30}最后", 0.2, "首先/其次/最后三段式"),
    (r"随着.{1,15}的发展", 0.2, "「随着…的发展」AI 开场白"),
    (r"分水岭", 0.2, "「分水岭」AI 夸大用语"),
]

# ═══ 字数/结构规则 ═══
MIN_CHARS = 800
MAX_CHARS = 4000
MIN_FIRST_PERSON = 5      # 每2000字最少5次「我」
MAX_BOLD_PER_1K = 3        # 每千字最多3处加粗
MAX_DASH_PER_1K = 2        # 每千字最多2个破折号


def check_article(article: str, title: str = "") -> dict:
    """
    对文章执行全量规则检查。
    返回 {
        penalties: float,           # 总扣分（从10分中减去）
        violations: [               # 违规列表
            {rule, severity, detail, suggestion}
        ],
        rewrite_directives: [       # 结构化修正指令（可直接传给 Writer）
            {dimension, action, severity}
        ],
        stats: {                    # 统计信息
            char_count, first_person_count, ai_keyword_hits, ...
        }
    }
    """
    violations = []
    rewrite_directives = []
    stats = {}

    if not article or len(article) < 50:
        return {
            "penalties": 5.0,
            "violations": [{"rule": "empty", "severity": "FATAL",
                          "detail": "文章内容过短或为空", "suggestion": "需要重新生成完整文章"}],
            "rewrite_directives": [
                {"dimension": "overall", "action": "文章内容过短，需重新生成完整内容", "severity": "critical"}
            ],
            "stats": {"char_count": len(article) if article else 0},
        }

    char_count = len(article)
    stats["char_count"] = char_count
    k_factor = char_count / 1000  # 千字系数

    # ── 字数检查 ──
    if char_count < MIN_CHARS:
        penalty = min(2.0, (MIN_CHARS - char_count) / MIN_CHARS * 3)
        violations.append({
            "rule": "min_length", "severity": "high",
            "detail": f"字数 {char_count}，低于下限 {MIN_CHARS}",
            "suggestion": f"需扩展 {MIN_CHARS - char_count} 字以上"
        })
        rewrite_directives.append({
            "dimension": "overall",
            "action": f"文章仅{char_count}字，太短，需扩展到{MIN_CHARS}字以上，增加具体案例和数据",
            "severity": "critical"
        })
    elif char_count > MAX_CHARS:
        violations.append({
            "rule": "max_length", "severity": "low",
            "detail": f"字数 {char_count}，超过上限 {MAX_CHARS}",
            "suggestion": f"需精简 {char_count - MAX_CHARS} 字"
        })
        rewrite_directives.append({
            "dimension": "overall",
            "action": f"文章{char_count}字过长，需精简到{MAX_CHARS}字以内",
            "severity": "minor"
        })

    # ── AI味关键词检测 ──
    keyword_hits = Counter()
    for keyword, penalty_weight in AI_FLAVOR_KEYWORDS.items():
        count = article.count(keyword)
        if count > 0:
            keyword_hits[keyword] = count

    ai_penalty = 0.0
    for kw, cnt in keyword_hits.items():
        weight = AI_FLAVOR_KEYWORDS[kw]
        ai_penalty += weight * cnt

    # 正则模式检测
    pattern_hits = []
    for pattern, weight, desc in AI_FLAVOR_PATTERNS:
        matches = re.findall(pattern, article)
        if matches:
            ai_penalty += weight * len(matches)
            pattern_hits.append(desc)
            keyword_hits[desc] = len(matches)

    ai_penalty = min(ai_penalty, 3.0)  # AI味扣分上限3分
    stats["ai_keyword_hits"] = dict(keyword_hits)
    stats["ai_penalty"] = round(ai_penalty, 2)

    if ai_penalty > 0.5:
        top_keywords = ", ".join([f"「{kw}」x{cnt}" for kw, cnt in keyword_hits.most_common(5)])
        violations.append({
            "rule": "ai_flavor", "severity": "high" if ai_penalty > 1.5 else "medium",
            "detail": f"AI味关键词扣分 {ai_penalty:.1f}，命中：{top_keywords}",
            "suggestion": "删除或替换上述关键词"
        })
        rewrite_directives.append({
            "dimension": "human_like",
            "action": f"删除AI味用词：{top_keywords}。用日常口语替代",
            "severity": "critical" if ai_penalty > 1.5 else "major"
        })

    # ── 第一人称检测 ──
    first_person_patterns = [
        r"我(?!们)",  # 排除「我们」
    ]
    first_person_count = len(re.findall(r"我(?!们)", article))
    expected_min = int(MIN_FIRST_PERSON * char_count / 2000)
    stats["first_person_count"] = first_person_count

    if first_person_count < expected_min:
        violations.append({
            "rule": "first_person", "severity": "medium",
            "detail": f"第一人称「我」出现 {first_person_count} 次，期望 ≥{expected_min}",
            "suggestion": "增加作者视角表达"
        })
        rewrite_directives.append({
            "dimension": "human_like",
            "action": f"「我」出现次数太少（{first_person_count}次），需增加真实个人体验和主观判断",
            "severity": "major"
        })

    # ── Markdown 残留检测 ──
    md_patterns = [
        (r"^\s*#{1,3}\s", "Markdown标题 #"),
        (r"\*\*[^*]+\*\*", "Markdown加粗 **"),
        (r"^\s*-\s", "Markdown列表 -"),
    ]
    md_hits = 0
    md_details = []
    for pattern, desc in md_patterns:
        matches = re.findall(pattern, article, re.MULTILINE)
        if matches:
            md_hits += len(matches)
            md_details.append(f"{desc} x{len(matches)}")

    if md_hits > 3:
        violations.append({
            "rule": "markdown_format", "severity": "medium",
            "detail": f"Markdown格式残留 {md_hits} 处：{', '.join(md_details)}",
            "suggestion": "微信公众号不支持Markdown，需改为纯文本格式"
        })
        rewrite_directives.append({
            "dimension": "readability",
            "action": "去除Markdown格式（#标题、**加粗**、-列表），用纯文本+空行排版",
            "severity": "major"
        })

    # ── 加粗/破折号密度 ──
    bold_count = len(re.findall(r"\*\*[^*]+\*\*", article))
    dash_count = article.count("——")
    max_bold = int(MAX_BOLD_PER_1K * k_factor) + 1
    max_dash = int(MAX_DASH_PER_1K * k_factor) + 1

    if bold_count > max_bold:
        violations.append({
            "rule": "bold_density", "severity": "low",
            "detail": f"加粗 {bold_count} 处，每千字上限 {MAX_BOLD_PER_1K}",
            "suggestion": "减少加粗，用【】或「」替代"
        })

    if dash_count > max_dash:
        violations.append({
            "rule": "dash_density", "severity": "low",
            "detail": f"破折号 {dash_count} 个，每千字上限 {MAX_DASH_PER_1K}",
            "suggestion": "减少破折号"
        })

    # ── 段落长度 ──
    paragraphs = [p.strip() for p in article.split("\n") if p.strip()]
    long_paragraphs = [p for p in paragraphs if len(p) > 200]
    if long_paragraphs:
        violations.append({
            "rule": "paragraph_length", "severity": "low",
            "detail": f"{len(long_paragraphs)} 个段落超过200字",
            "suggestion": "拆分为更短的段落（每段2-3句）"
        })
        rewrite_directives.append({
            "dimension": "readability",
            "action": f"有{len(long_paragraphs)}个超长段落，需拆分为每段2-3句、100字以内",
            "severity": "minor"
        })

    # ── 总扣分 ──
    total_penalty = ai_penalty
    if char_count < MIN_CHARS:
        total_penalty += min(1.0, penalty)
    total_penalty = min(total_penalty, 4.0)  # 规则层总扣分上限4分

    return {
        "penalties": round(total_penalty, 2),
        "violations": violations,
        "rewrite_directives": rewrite_directives,
        "stats": stats,
    }
