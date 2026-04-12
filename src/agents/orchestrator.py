"""
Agent: Orchestrator - 主题分类 + 写作策略选择
"""
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from llm import create_llm
from utils.config import config
from utils.logger import logger
from utils.json_parser import parse_llm_json


def orchestrator_node(state: dict, run_config=None) -> dict:
    """分析关键词，确定主题分类、文章结构模式、目标读者"""
    keyword = state.get("topic_keyword", "科技")
    logger.info(f"🎯 Orchestrator: 分析关键词 '{keyword}'")

    try:
        llm = create_llm("orchestrator")
        system_prompt = config.load_prompt("orchestrator")
        user_prompt = f"关键词：{keyword}"

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)

        result = parse_llm_json(
            response.content,
            expected_keys=["topic_category", "article_pattern", "target_audience", "writing_strategy"],
        )

        category = result.get("topic_category", "tech_trends")
        pattern = result.get("article_pattern", "essay")
        audience = result.get("target_audience", "泛科技读者")
        strategy = result.get("writing_strategy", {})

        logger.info(f"✅ 分类: {category}, 结构: {pattern}, 读者: {audience}")

        return {
            "topic_category": category,
            "article_pattern": pattern,
            "target_audience": audience,
            "writing_strategy": strategy,
            "write_round": 0,
            "regroup_round": state.get("regroup_round", 0),
        }

    except Exception as e:
        logger.error(f"❌ Orchestrator 失败: {e}")
        return {
            "topic_category": "tech_trends",
            "article_pattern": "essay",
            "target_audience": "泛科技读者",
            "writing_strategy": {},
            "write_round": 0,
            "regroup_round": state.get("regroup_round", 0),
            "errors": [{"node": "orchestrator", "error": str(e), "severity": "DEGRADABLE", "timestamp": ""}],
        }
