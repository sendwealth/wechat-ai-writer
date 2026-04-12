"""
Agent: Research - 搜索 + 筛选 + 提取关键数据
"""
from datetime import datetime, timedelta
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from search import create_search
from llm import create_llm
from utils.config import config
from utils.logger import logger
from utils.retry import with_retry
from utils.json_parser import parse_llm_json


def _do_search(query: str, count: int) -> list:
    """执行搜索（可被重试装饰器包装）"""
    search = create_search()
    return search.search(query, count)


def research_node(state: dict, run_config=None) -> dict:
    """搜索新闻 → 筛选高质量源 → 提取关键数据点"""
    keyword = state.get("topic_keyword", "科技")
    strategy = state.get("writing_strategy", {})
    max_results = config.get("agents.research.max_results", 8)
    recency_days = config.get("agents.research.recency_days", 7)

    logger.info(f"🔍 Research: 搜索 '{keyword}'")

    try:
        # 1. 搜索新闻
        end_date = datetime.now()
        start_date = end_date - timedelta(days=recency_days)
        date_filter = f"after:{start_date.strftime('%Y-%m-%d')}"

        query = f"{keyword} 最新 数据 案例 {date_filter}"
        logger.info(f"   查询: {query}")

        try:
            search_results = _do_search(query, max_results)
        except Exception as e:
            logger.warning(f"⚠️ 搜索失败，尝试简化查询: {e}")
            search_results = _do_search(keyword, max_results)

        logger.info(f"   找到 {len(search_results)} 条结果")

        if not search_results:
            return {
                "search_results": [],
                "curated_references": [],
                "key_data_points": [f"关于{keyword}的最新资讯"],
                "errors": [{"node": "research", "error": "搜索无结果", "severity": "DEGRADABLE", "timestamp": ""}],
            }

        # 2. LLM 筛选 + 提取数据点
        llm = create_llm("research")
        system_prompt = config.load_prompt("research_filter")

        articles_text = ""
        for i, item in enumerate(search_results[:8], 1):
            articles_text += f"\n[{i}] 标题: {item.get('title', '')}\n    来源: {item.get('source', '')}\n    链接: {item.get('url', '')}\n    摘要: {item.get('snippet', '')}\n"

        user_prompt = f"主题: {keyword}\n\n搜索结果:\n{articles_text}\n\n请筛选并提取关键数据点。"

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)

        result = parse_llm_json(
            response.content,
            expected_keys=["curated_references", "key_data_points"],
        )

        curated = result.get("curated_references", search_results[:5])
        data_points = result.get("key_data_points", [])

        logger.info(f"✅ 筛选 {len(curated)} 篇参考，提取 {len(data_points)} 个数据点")

        return {
            "search_results": search_results,
            "curated_references": curated,
            "key_data_points": data_points,
        }

    except Exception as e:
        logger.error(f"❌ Research 失败: {e}")
        return {
            "search_results": [],
            "curated_references": state.get("search_results", [])[:5],
            "key_data_points": [],
            "errors": [{"node": "research", "error": str(e), "severity": "DEGRADABLE", "timestamp": ""}],
        }
