"""
Agent: Critic - 规则预检 + 七维LLM评分 + 结构化修正指令
Loop Engineering 核心：评估结果转化为可执行指令
"""
from langchain_core.messages import SystemMessage, HumanMessage
from llm import create_llm
from utils.config import config
from utils.logger import logger
from utils.json_parser import parse_llm_json
from utils.rule_check import check_article


# 权重配置（新增 human_like 维度，权重30%）
WEIGHTS = {
    "hook": 0.15,
    "structure": 0.10,
    "persuasiveness": 0.15,
    "readability": 0.10,
    "originality": 0.10,
    "cta": 0.10,
    "human_like": 0.30,
}


def _build_rewrite_directives(rule_result: dict, scores: list, suggestions: list, threshold: float) -> list:
    """
    将规则违规 + LLM 低分维度 + 改进建议 → 统一的结构化修正指令
    这是 Loop Engineering 的核心：评估结果必须转化为下一轮的具体可执行指令
    """
    directives = []

    # 1. 规则层修正指令（确定性、高优先）
    directives.extend(rule_result.get("rewrite_directives", []))

    # 2. LLM 低分维度 → 结构化指令
    for s in scores:
        if not isinstance(s, dict):
            continue
        dim = s.get("dimension", "")
        score = s.get("score", 10)
        feedback = s.get("feedback", "")

        if score < 7.0:
            severity = "critical" if score < 5.0 else ("major" if score < 6.0 else "minor")
            directives.append({
                "dimension": dim,
                "action": feedback if feedback else f"{dim}维度得分{score}，需提升到{threshold}",
                "severity": severity,
            })

    # 3. LLM 改进建议（补充上下文）
    for suggestion in suggestions[:3]:
        directives.append({
            "dimension": "overall",
            "action": suggestion,
            "severity": "minor",
        })

    # 按 severity 排序：critical > major > minor
    severity_order = {"critical": 0, "major": 1, "minor": 2}
    directives.sort(key=lambda d: severity_order.get(d.get("severity", "minor"), 3))

    return directives


def critic_node(state: dict, run_config=None) -> dict:
    """规则预检 + LLM 多维度评分 + 生成结构化修正指令"""
    article = state.get("draft_article", state.get("edited_article", ""))
    title = state.get("selected_title", state.get("topic_keyword", ""))
    threshold = config.get("workflow.quality_threshold", 7.5)
    write_round = state.get("write_round", 1)

    logger.info(f"🔍 Critic: 评审文章 (第{write_round}轮)")

    # ── 空文章快速短路 ──
    if not article or len(article) < 100:
        logger.warning("⚠️ 文章内容过短，直接标记为不达标")
        return {
            "quality_scores": [
                {"dimension": d, "score": 3.0, "feedback": "文章内容过短"}
                for d in WEIGHTS.keys()
            ],
            "overall_score": 3.0,
            "critic_feedback": "文章内容过短，需要大幅扩展。",
            "rewrite_directives": [
                {"dimension": "overall", "action": "文章内容过短，需重新生成完整内容", "severity": "critical"}
            ],
        }

    # ═══ 第一步：规则预检（零 token 成本） ═══
    rule_result = check_article(article, title)
    rule_penalty = rule_result["penalties"]
    rule_violations = rule_result["violations"]
    rule_stats = rule_result["stats"]

    if rule_violations:
        logger.info(f"📋 规则预检: 扣分 {rule_penalty}, {len(rule_violations)} 项违规")
        for v in rule_violations[:3]:
            logger.info(f"   ⚠️ [{v['severity']}] {v['detail']}")

    # ═══ 第二步：LLM 七维评分 ═══
    try:
        llm = create_llm("critic")
        system_prompt = config.load_prompt("critic")

        # 如果规则预检发现AI味关键词，注入提示让 LLM 重点关注
        ai_hits = rule_stats.get("ai_keyword_hits", {})
        rule_hint = ""
        if ai_hits:
            top_kw = list(ai_hits.keys())[:5]
            rule_hint = f"\n\n[规则预检提示] 已检测到AI味用词：{', '.join(top_kw)}。请在human_like维度严格扣分。"

        user_prompt = f"""评分文章：{title}

{article}
{rule_hint}

要求：输出紧凑JSON，包含7个维度（hook/structure/persuasiveness/readability/originality/cta/human_like），每个feedback不超过20个字。格式：
{{"scores":[{{"dimension":"hook","score":8,"feedback":"xxx"}}...],"overall_score":8.0,"summary":"xxx","improvement_suggestions":["xxx"]}}"""

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)

        result = parse_llm_json(
            response.content,
            expected_keys=["scores", "overall_score", "summary", "improvement_suggestions"],
        )

        scores = result.get("scores", [])
        summary = result.get("summary", "")
        suggestions = result.get("improvement_suggestions", [])

        # 如果 scores 是 dict 而非 list（正则兜底场景），转为 list
        if isinstance(scores, dict):
            scores = [{"dimension": k, "score": v if isinstance(v, (int, float)) else v.get("score", 5.0), "feedback": ""} for k, v in scores.items()]

        # 计算加权总分
        total = 0.0
        for s in scores:
            if not isinstance(s, dict):
                continue
            dim = s.get("dimension", "")
            score = s.get("score", 5.0)
            weight = WEIGHTS.get(dim, 0.10)
            total += score * weight

        llm_overall = round(total, 1)

        # ═══ 第三步：规则扣分合并 ═══
        # 最终分数 = LLM评分 - 规则扣分（保底 1.0）
        overall = max(1.0, round(llm_overall - rule_penalty, 1))

        feedback = summary
        if suggestions:
            feedback += "\n改进建议:\n" + "\n".join([f"- {s}" for s in suggestions])
        if rule_violations:
            feedback += f"\n规则预检: 扣{rule_penalty}分"

        # ═══ 第四步：生成结构化修正指令 ═══
        rewrite_directives = _build_rewrite_directives(
            rule_result, scores, suggestions, threshold
        )

        status = "✅ 达标" if overall >= threshold else "❌ 不达标"
        logger.info(f"{status} 总分: {overall}/{threshold} (LLM: {llm_overall}, 规则扣: {rule_penalty})")

        # ═══ 维度地板检查：关键维度太低也判不达标 ═══
        DIMENSION_FLOOR = {
            "human_like": 8.0,  # AI 味重不可接受
            "hook": 7.5,        # 开头无聊没人看
        }
        floor_failed = False
        for s in scores:
            if not isinstance(s, dict):
                continue
            dim = s.get("dimension", "")
            sc = s.get("score", 0)
            floor = DIMENSION_FLOOR.get(dim)
            if floor and sc < floor:
                floor_failed = True
                logger.warning(f"   ⚠️ 维度地板: {dim}={sc} < {floor}")
                # 确保有一条对应的修正指令
                if not any(d.get("dimension") == dim for d in rewrite_directives):
                    rewrite_directives.append({
                        "dimension": dim,
                        "action": f"{dim}维度得分{sc}低于地板线{floor}，必须提升",
                        "severity": "major",
                    })
        if floor_failed and overall >= threshold:
            logger.warning(f"   ⚠️ 总分达标但维度地板未过，降级为不达标")
            overall = threshold - 0.1  # 强制进入重写
        for s in scores:
            if not isinstance(s, dict):
                continue
            dim = s.get("dimension", "")
            sc = s.get("score", 0)
            bar = "█" * int(sc) + "░" * (10 - int(sc))
            logger.info(f"   {dim:16s} [{bar}] {sc}/10")

        if rewrite_directives:
            logger.info(f"   → 生成 {len(rewrite_directives)} 条修正指令")

        # 记录分数到历史
        score_history = list(state.get("score_history", []))
        score_history.append(overall)

        # ═══ 第五步：追踪最佳版本 ═══
        best_draft = state.get("best_draft", "")
        best_score = state.get("best_score", 0)
        state_updates = {}

        if overall > best_score:
            best_score = overall
            best_draft = article
            logger.info(f"   ⭐ 新最佳版本: {overall} 分")
            state_updates["best_draft"] = best_draft
            state_updates["best_score"] = best_score

        return {
            "quality_scores": scores,
            "overall_score": overall,
            "critic_feedback": feedback,
            "rewrite_directives": rewrite_directives,
            "rule_check_result": rule_result,
            "score_history": score_history,
            **state_updates,
        }

    except Exception as e:
        logger.error(f"❌ Critic 失败: {e}")
        return {
            "quality_scores": [],
            "overall_score": max(1.0, 5.0 - rule_penalty),
            "critic_feedback": f"评审失败: {str(e)}",
            "rewrite_directives": rule_result.get("rewrite_directives", []),
            "rule_check_result": rule_result,
            "errors": [{"node": "critic", "error": str(e), "severity": "DEGRADABLE", "timestamp": ""}],
        }
