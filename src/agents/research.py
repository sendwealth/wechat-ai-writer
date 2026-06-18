"""
Agent: Research - 多路搜索 + 全文抓取 + 筛选 + 提取关键数据
"""
import re
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


def _fetch_article_content(url: str, timeout: int = 8) -> str:
    """抓取页面全文，提取 <p> 标签文本（前 500 字）"""
    try:
        import httpx
        resp = httpx.get(url, timeout=timeout, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        resp.raise_for_status()
        html = resp.text
        # 提取 <p> 标签内容
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
        text = " ".join(re.sub(r'<[^>]+>', '', p) for p in paragraphs)
        # 清理空白，取前 500 字
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:500] if text else ""
    except Exception:
        return ""


def _deduplicate(results: list) -> list:
    """按 URL 去重"""
    seen_urls = set()
    deduped = []
    for item in results:
        url = item.get("url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        deduped.append(item)
    return deduped


def research_node(state: dict, run_config=None) -> dict:
    """多路搜索（新闻+数据+观点） → 全文抓取 → LLM 筛选"""
    keyword = state.get("topic_keyword", "科技")
    strategy = state.get("writing_strategy", {})
    per_query = config.get("agents.research.max_results", 5)
    recency_days = config.get("agents.research.recency_days", 7)
    fetch_count = config.get("agents.research.content_fetch_count", 3)

    logger.info(f"🔍 Research: 搜索 '{keyword}'")

    try:
        search = create_search()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=recency_days)

        # ── 三路搜索 ──
        all_results = []

        # 1. 新闻搜索（Google News，天然最新）
        try:
            news = search.search_news(keyword, per_query)
            for r in news:
                r["_source_type"] = "news"
            all_results.extend(news)
            logger.info(f"   新闻: {len(news)} 条")
        except Exception as e:
            logger.warning(f"⚠️ 新闻搜索失败: {e}")

        # 2. 数据/报告搜索（普通搜索 + 时间过滤）
        data_query = f"{keyword} 数据 统计 报告"
        try:
            data_results = search.search(data_query, per_query, tbs="qdr:w")
            for r in data_results:
                r["_source_type"] = "data"
            all_results.extend(data_results)
            logger.info(f"   数据: {len(data_results)} 条")
        except Exception as e:
            logger.warning(f"⚠️ 数据搜索失败: {e}")

        # 3. 观点/评测搜索（限近一个月，要深度分析）
        opinion_query = f"{keyword} 案例 评测 观点"
        try:
            opinion_results = search.search(opinion_query, per_query, tbs="qdr:m")
            for r in opinion_results:
                r["_source_type"] = "opinion"
            all_results.extend(opinion_results)
            logger.info(f"   观点: {len(opinion_results)} 条")
        except Exception as e:
            logger.warning(f"⚠️ 观点搜索失败: {e}")

        # 去重
        all_results = _deduplicate(all_results)
        logger.info(f"   合计（去重后）: {len(all_results)} 条")

        if not all_results:
            return {
                "search_results": [],
                "curated_references": [],
                "key_data_points": [f"关于{keyword}的最新资讯"],
                "errors": [{"node": "research", "error": "三路搜索均无结果", "severity": "DEGRADABLE", "timestamp": ""}],
            }

        # ── 全文抓取（对新闻结果的前 N 条）──
        news_items = [r for r in all_results if r.get("_source_type") == "news"]
        for item in news_items[:fetch_count]:
            url = item.get("url", "")
            if not url:
                continue
            content = _fetch_article_content(url)
            if content:
                item["content"] = content
                logger.info(f"   📄 抓取全文: {item.get('title', '')[:30]}... ({len(content)} 字)")

        # 清理内部标记
        for r in all_results:
            r.pop("_source_type", None)

        # ── LLM 筛选 + 提取数据点 ──
        llm = create_llm("research")
        system_prompt = config.load_prompt("research_filter")

        articles_text = ""
        for i, item in enumerate(all_results[:15], 1):
            date_str = item.get("date", "")
            content = item.get("content", "")
            text = f"\n[{i}] 标题: {item.get('title', '')}\n"
            text += f"    来源: {item.get('source', '')}\n"
            if date_str:
                text += f"    日期: {date_str}\n"
            text += f"    摘要: {item.get('snippet', '')}\n"
            if content:
                text += f"    全文: {content}\n"

            articles_text += text

        user_prompt = f"主题: {keyword}\n当前日期: {end_date.strftime('%Y-%m-%d')}\n\n搜索结果:\n{articles_text}\n\n请筛选并提取关键数据点。丢弃任何早于 {start_date.strftime('%Y-%m-%d')} 的过时内容。"

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)

        result = parse_llm_json(
            response.content,
            expected_keys=["curated_references", "key_data_points"],
        )

        curated = result.get("curated_references", all_results[:5])
        data_points = result.get("key_data_points", [])

        logger.info(f"✅ 筛选 {len(curated)} 篇参考，提取 {len(data_points)} 个数据点")

        return {
            "search_results": all_results,
            "curated_references": curated,
            "key_data_points": data_points,
        }

    except Exception as e:
        logger.error(f"❌ Research 失败: {e}")
        return {
            "search_results": [],
            "curated_references": [],
            "key_data_points": [],
            "errors": [{"node": "research", "error": str(e), "severity": "DEGRADABLE", "timestamp": ""}],
        }
