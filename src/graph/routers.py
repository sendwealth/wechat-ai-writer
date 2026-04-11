"""
路由函数 - LangGraph 条件边的决策逻辑
"""
from utils.config import config
from utils.logger import logger


def route_after_critic(state: dict) -> str:
    """
    Critic 评分后的路由：
    - 达标 → editor（润色）
    - 不达标且轮次未满 → writer（重写）
    - 不达标但轮次已满 → editor（强制走润色，保守输出）
    """
    overall_score = state.get("overall_score", 0)
    write_round = state.get("write_round", 0)
    threshold = config.get("workflow.quality_threshold", 7.5)
    max_rounds = config.get("workflow.max_write_rounds", 5)

    if overall_score >= threshold:
        logger.info(f"🟢 Critic 达标: {overall_score} >= {threshold} → Editor")
        return "editor"
    elif write_round < max_rounds:
        logger.info(f"🔴 Critic 不达标: {overall_score} < {threshold} (第{write_round}/{max_rounds}轮) → 重写")
        return "rewrite"
    else:
        logger.info(f"🟡 Critic 轮次耗尽: {write_round}/{max_rounds}，分数 {overall_score} → 强制走 Editor")
        return "editor"


def route_final(state: dict) -> str:
    """
    终审路由：
    - 达标 → publisher
    - 不达标且降级次数未满 → orchestrator（换结构重做）
    - 降级次数耗尽 → publisher（以现有最好结果发布）
    """
    overall_score = state.get("overall_score", 0)
    regroup_round = state.get("regroup_round", 0)
    final_threshold = config.get("workflow.final_threshold", 7.0)
    max_regroup = config.get("workflow.max_regroup_rounds", 2)

    if overall_score >= final_threshold:
        logger.info(f"🟢 终审通过: {overall_score} >= {final_threshold} → 发布")
        return "publish"
    elif regroup_round < max_regroup:
        # 选择另一种结构模式
        patterns = ["conflict", "listicle", "story", "essay"]
        current = state.get("article_pattern", "essay")
        remaining = [p for p in patterns if p != current]
        import random
        new_pattern = random.choice(remaining) if remaining else "essay"

        logger.info(
            f"🟡 终审不达标: {overall_score} < {final_threshold} "
            f"(降级{regroup_round+1}/{max_regroup}) "
            f"换结构: {current} → {new_pattern}"
        )
        # 通过返回 regroup，在 workflow 中处理状态更新
        return "regroup"
    else:
        logger.info(
            f"🟠 降级次数耗尽: {regroup_round}/{max_regroup}，"
            f"分数 {overall_score}，以当前结果发布"
        )
        return "publish"
