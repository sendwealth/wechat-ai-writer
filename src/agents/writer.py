"""
Agent: Writer - 分节写作 + 反馈注入
"""
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from llm import create_llm
from utils.config import config
from utils.logger import logger


def _build_writer_prompt(state: dict) -> tuple:
    """动态组合写作 Prompt"""
    base = config.load_prompt("writer")
    pattern = state.get("article_pattern", "essay")
    pattern_prompt = config.load_prompt(f"writer_{pattern}")

    system = base + "\n\n" + pattern_prompt

    # 反馈注入（非第一轮时）
    write_round = state.get("write_round", 0)
    feedback_section = ""
    if write_round > 0:
        critic_feedback = state.get("critic_feedback", "")
        quality_scores = state.get("quality_scores", [])
        low_dims = [s for s in quality_scores if s.get("score", 10) < 7.0]

        if low_dims or critic_feedback:
            feedback_section = "\n\n## 上一轮评审反馈（请针对性改进）\n"
            if critic_feedback:
                feedback_section += f"总结: {critic_feedback}\n"
            for dim in low_dims:
                feedback_section += f"- [{dim.get('dimension', '')}] 分数{dim.get('score', 0)}/10: {dim.get('feedback', '')}\n"
            feedback_section += "\n请重点改进以上薄弱维度，保持已达标部分不变。\n"

    # 参考资料和大纲
    outline = state.get("outline", {})
    references = state.get("curated_references", [])
    data_points = state.get("key_data_points", [])
    title = state.get("selected_title", state.get("topic_keyword", "科技"))

    refs_text = ""
    for i, ref in enumerate(references[:5], 1):
        refs_text += f"\n[{i}] {ref.get('title', '')} ({ref.get('source', '')})\n    {ref.get('snippet', '')}"

    data_text = "\n".join([f"- {d}" for d in data_points[:8]])

    import json
    outline_text = json.dumps(outline, ensure_ascii=False, indent=2)

    user = f"""## 文章标题
{title}

## 文章大纲
{outline_text}

## 参考资料
{refs_text}

## 关键数据点
{data_text}

{feedback_section}

请按照大纲和写作规则，撰写一篇完整的微信公众号文章。直接输出文章内容，不要任何开场白。"""

    return system, user


def writer_node(state: dict, run_config=None) -> dict:
    """按大纲写作，注入评审反馈"""
    write_round = state.get("write_round", 0) + 1
    max_rounds = config.get("workflow.max_write_rounds", 5)

    logger.info(f"✍️ Writer: 第 {write_round}/{max_rounds} 轮写作")

    try:
        system_prompt, user_prompt = _build_writer_prompt(state)

        # 根据轮次调整温度（越往后越保守）
        base_temp = config.get("agents.writer.temperature", 0.85)
        decay = config.get("agents.writer.temperature_decay", 0.1)
        adjusted_temp = max(0.3, base_temp - (write_round - 1) * decay)

        llm = create_llm("writer")
        # 临时调整温度
        llm.llm.temperature = adjusted_temp
        logger.info(f"   温度: {adjusted_temp:.2f}")

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)
        article = response.content.strip()

        # Token 使用监控
        _log_token_usage(response, f"writer-r{write_round}")

        logger.info(f"✅ 写作完成: {len(article)} 字符")

        return {
            "draft_article": article,
            "write_round": write_round,
        }

    except Exception as e:
        logger.error(f"❌ Writer 失败: {e}")
        return {
            "draft_article": f"{state.get('selected_title', '未知')}\n\n写作失败，请重试。",
            "write_round": write_round,
            "errors": [{"node": "writer", "error": str(e), "severity": "RETRYABLE", "timestamp": ""}],
        }


def _log_token_usage(response, agent_name: str):
    """记录 LLM 响应的 token 使用量"""
    try:
        meta = getattr(response, 'response_metadata', {}) or {}
        token_usage = meta.get('token_usage', {}) or meta.get('usage', {}) or {}
        prompt_tokens = token_usage.get('prompt_tokens', 0)
        completion_tokens = token_usage.get('completion_tokens', 0)
        total = token_usage.get('total_tokens', prompt_tokens + completion_tokens)

        if completion_tokens > 0:
            logger.info(f"   📊 [{agent_name}] tokens: prompt={prompt_tokens}, completion={completion_tokens}, total={total}")
    except Exception:
        pass
