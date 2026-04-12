"""
Agent: Title Generator - 生成 + 混合评分候选标题
"""
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from llm import create_llm
from utils.config import config
from utils.logger import logger
from utils.json_parser import parse_llm_json


# ── 规则评分（满分100）──

def _rule_score(title: str) -> dict:
    """规则评分：好奇缺口(30) + 价值承诺(25) + 身份认同(20) + 数字符号(15) + 长度(10)"""
    details = {}

    # 好奇缺口 (30)
    score = 0
    if any(w in title for w in ['这', '那个', '没想到', '原来', '竟然', '居然', '为什么', '如何', '什么']):
        score += 10
    if '？' in title or '?' in title:
        score += 10
    if any(w in title for w in ['最后', '结果', '真相', '秘密', '惊人']):
        score += 10
    details['curiosity_gap'] = min(score, 30)

    # 价值承诺 (25)
    score = 0
    if any(c.isdigit() for c in title):
        score += 10
    if any(w in title for w in ['提升', '提高', '增加', '减少', '节省', '学会', '掌握', '获得']):
        score += 10
    if any(w in title for w in ['附', '完整', '详细', '教程', '指南', '清单', '资源']):
        score += 5
    details['value_promise'] = min(score, 25)

    # 身份认同 (20)
    score = 0
    if any(w in title for w in ['普通人', '程序员', '打工人', '学生', '创业者', '职场人', '小白', '新手']):
        score += 20
    details['identity'] = min(score, 20)

    # 数字符号 (15)
    score = 0
    if any(c.isdigit() for c in title):
        score += 10
    if any(s in title for s in ['【', '】', '！', '？', '🔥', '⭐', '✅', '💡']):
        score += 5
    details['numbers_symbols'] = min(score, 15)

    # 长度 (10)
    length = len(title)
    if 20 <= length <= 35:
        details['length'] = 10
    elif 15 <= length <= 40:
        details['length'] = 5
    else:
        details['length'] = 0

    total = sum(details.values())
    return {'score': total, 'details': details}


def _batch_llm_score(titles: list, topic: str) -> dict:
    """一次性 LLM 批量评分所有标题。返回 {title_text: avg_score}"""
    if not titles:
        return {}

    try:
        llm = create_llm("title")

        # 构造批量评分 prompt
        titles_list = "\n".join([f'{i+1}. "{t}"' for i, t in enumerate(titles)])
        user_prompt = f"""请对以下 {len(titles)} 个微信公众号文章标题逐个评分。

主题：{topic}

评分维度（每项 0-10 分，取平均分）：
- 点击欲望：看到标题是否想点进去？
- 信息承诺：标题是否暗示了有价值的内容？
- 情绪触发：是否引发好奇/焦虑/惊喜等情绪？
- 真实可信：不像标题党，感觉可信？

标题列表：
{titles_list}

输出 JSON 格式（紧凑）：
{{"scores": [{{"index": 1, "avg_score": 7.5}}, ...]}}

只输出 JSON。"""

        messages = [HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)

        result = parse_llm_json(
            response.content,
            expected_keys=["scores"],
        )

        # 构建映射: title -> score
        score_map = {}
        score_list = result.get("scores", [])
        for i, item in enumerate(score_list):
            idx = item.get("index", i + 1) - 1
            if 0 <= idx < len(titles):
                score_map[titles[idx]] = item.get("avg_score", 6.0)

        return score_map

    except Exception as e:
        logger.warning(f"⚠️ LLM 批量标题评分失败: {e}")
        return {}


def title_generator_node(state: dict, run_config=None) -> dict:
    """生成多个候选标题，混合评分选出最佳"""
    keyword = state.get("topic_keyword", "科技")
    category = state.get("topic_category", "tech_trends")
    data_points = state.get("key_data_points", [])
    audience = state.get("target_audience", "泛科技读者")

    rule_weight = config.get("agents.title.rule_weight", 0.4)
    llm_weight = config.get("agents.title.llm_weight", 0.6)

    logger.info(f"📝 TitleGenerator: 生成候选标题")

    try:
        # 1. LLM 生成候选标题
        llm = create_llm("title")
        prompt_template = config.load_prompt("title_generator")

        user_prompt = prompt_template.replace("{topic}", keyword)
        user_prompt = user_prompt.replace("{category}", category)
        user_prompt = user_prompt.replace("{data_points}", "、".join(data_points[:5]))
        user_prompt = user_prompt.replace("{audience}", audience)

        messages = [HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)

        result = parse_llm_json(
            response.content,
            expected_keys=["titles"],
        )
        raw_titles = result.get("titles", [])

        if not raw_titles:
            raw_titles = [{"title": keyword, "strategy": "direct"}]

        # 2. 批量 LLM 评分（1 次调用替代 N 次）
        title_texts = [item.get("title", keyword) for item in raw_titles]
        llm_scores = _batch_llm_score(title_texts, keyword)

        # 3. 混合评分
        candidates = []
        for item in raw_titles:
            title = item.get("title", keyword)
            strategy = item.get("strategy", "")

            # 规则评分 (0-100)
            rule = _rule_score(title)

            # LLM 评分 (0-10 → 缩放到 0-100)
            llm_score = llm_scores.get(title, 6.0) * 10

            # 加权
            final_score = rule['score'] * rule_weight + llm_score * llm_weight

            candidates.append({
                "title": title,
                "strategy": strategy,
                "rule_score": rule['score'],
                "rule_details": rule['details'],
                "llm_score": llm_score / 10,
                "final_score": round(final_score, 1),
            })

        # 排序
        candidates.sort(key=lambda x: x['final_score'], reverse=True)
        best = candidates[0]

        logger.info(f"✅ 生成 {len(candidates)} 个候选标题")
        for i, c in enumerate(candidates[:3], 1):
            logger.info(f"   {i}. {c['title']} (分: {c['final_score']})")
        logger.info(f"   最佳: {best['title']}")

        return {
            "title_candidates": candidates,
            "selected_title": best["title"],
            "title_score": best["final_score"],
        }

    except Exception as e:
        logger.error(f"❌ TitleGenerator 失败: {e}")
        return {
            "title_candidates": [],
            "selected_title": keyword,
            "title_score": 0,
            "errors": [{"node": "title_generator", "error": str(e), "severity": "DEGRADABLE", "timestamp": ""}],
        }
