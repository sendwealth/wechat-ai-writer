"""
Agent: Title Generator - 生成 + 混合评分候选标题
"""
import json
import re
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from llm import create_llm
from utils.config import config
from utils.logger import logger


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


def _llm_score_title(title: str, topic: str) -> dict:
    """LLM 评分"""
    try:
        llm = create_llm("title")
        prompt_template = config.load_prompt("title_scorer")
        user_prompt = prompt_template.replace("{title}", title).replace("{topic}", topic)

        messages = [HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)
        text = response.content.strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        return json.loads(text.strip())
    except Exception as e:
        logger.warning(f"⚠️ LLM 标题评分失败: {e}")
        return {"avg_score": 6.0}


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
        text = response.content.strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        result = json.loads(text.strip())
        raw_titles = result.get("titles", [])

        if not raw_titles:
            raw_titles = [{"title": keyword, "strategy": "direct"}]

        # 2. 混合评分
        candidates = []
        for item in raw_titles:
            title = item.get("title", keyword)
            strategy = item.get("strategy", "")

            # 规则评分 (0-100)
            rule = _rule_score(title)

            # LLM 评分 (0-10 → 缩放到 0-100)
            llm_result = _llm_score_title(title, keyword)
            llm_score = llm_result.get("avg_score", 6.0) * 10

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
