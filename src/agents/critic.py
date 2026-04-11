"""
Agent: Critic - 六维质量评分
"""
import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from llm import create_llm
from utils.config import config
from utils.logger import logger

# 权重配置
WEIGHTS = {
    "hook": 0.20,
    "structure": 0.15,
    "persuasiveness": 0.20,
    "readability": 0.15,
    "originality": 0.15,
    "cta": 0.15,
}


def _repair_json(text: str) -> dict:
    """尝试修复截断的 JSON"""
    # 先试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试补全截断的 JSON：找到最后一个完整的对象
    # 方法：逐个字符回退，找到可以解析的位置
    for i in range(len(text) - 1, max(10, len(text) - 500), -1):
        if text[i] == '}':
            try:
                result = json.loads(text[:i+1] + ']}')
                return result
            except json.JSONDecodeError:
                continue

    # 最后手段：用正则提取分数
    scores = []
    for dim in WEIGHTS.keys():
        match = re.search(rf'"{dim}".*?"score"\s*:\s*(\d+\.?\d*)', text)
        if match:
            scores.append({"dimension": dim, "score": float(match.group(1)), "feedback": ""})

    if scores:
        return {"scores": scores, "overall_score": 0, "summary": "JSON截断，正则提取分数", "improvement_suggestions": []}

    raise json.JSONDecodeError("无法修复 JSON", text, 0)


def critic_node(state: dict, run_config=None) -> dict:
    """多维度评分文章质量"""
    article = state.get("draft_article", state.get("edited_article", ""))
    outline = state.get("outline", {})
    title = state.get("selected_title", state.get("topic_keyword", ""))
    threshold = config.get("workflow.quality_threshold", 7.5)
    write_round = state.get("write_round", 1)

    logger.info(f"🔍 Critic: 评审文章 (第{write_round}轮)")

    if not article or len(article) < 100:
        logger.warning("⚠️ 文章内容过短，直接标记为不达标")
        return {
            "quality_scores": [
                {"dimension": d, "score": 3.0, "feedback": "文章内容过短"}
                for d in WEIGHTS.keys()
            ],
            "overall_score": 3.0,
            "critic_feedback": "文章内容过短，需要大幅扩展。",
        }

    try:
        llm = create_llm("critic")
        # 确保足够的 max_tokens
        llm.llm.max_tokens = 4000

        system_prompt = config.load_prompt("critic")

        # 精简 prompt，只发文章内容（不发大纲，减少 token）
        # 要求 LLM 输出紧凑的 JSON
        user_prompt = f"""评分文章：{title}

{article}

要求：输出紧凑JSON，每个feedback不超过20个字。格式：
{{"scores":[{{"dimension":"hook","score":8,"feedback":"xxx"}}...],"overall_score":8.0,"summary":"xxx","improvement_suggestions":["xxx"]}}"""

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)
        result_text = response.content.strip()

        # 提取 JSON
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]

        # 用修复逻辑解析
        result = _repair_json(result_text.strip())

        scores = result.get("scores", [])
        summary = result.get("summary", "")
        suggestions = result.get("improvement_suggestions", [])

        # 计算加权总分
        total = 0.0
        for s in scores:
            dim = s.get("dimension", "")
            score = s.get("score", 5.0)
            weight = WEIGHTS.get(dim, 0.15)
            total += score * weight

        overall = round(total, 1)
        feedback = summary
        if suggestions:
            feedback += "\n改进建议:\n" + "\n".join([f"- {s}" for s in suggestions])

        status = "✅ 达标" if overall >= threshold else "❌ 不达标"
        logger.info(f"{status} 总分: {overall}/{threshold}")
        for s in scores:
            dim = s.get("dimension", "")
            sc = s.get("score", 0)
            bar = "█" * int(sc) + "░" * (10 - int(sc))
            logger.info(f"   {dim:16s} [{bar}] {sc}/10")

        return {
            "quality_scores": scores,
            "overall_score": overall,
            "critic_feedback": feedback,
        }

    except Exception as e:
        logger.error(f"❌ Critic 失败: {e}")
        return {
            "quality_scores": [],
            "overall_score": 5.0,
            "critic_feedback": f"评审失败: {str(e)}",
            "errors": [{"node": "critic", "error": str(e), "severity": "DEGRADABLE", "timestamp": ""}],
        }
