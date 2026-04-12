"""
Agent: Outline - 生成结构化大纲
"""
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from llm import create_llm
from utils.config import config
from utils.logger import logger
from utils.json_parser import parse_llm_json


def outline_node(state: dict, run_config=None) -> dict:
    """根据文章结构模式生成大纲"""
    title = state.get("selected_title", state.get("topic_keyword", "科技"))
    pattern = state.get("article_pattern", "essay")
    references = state.get("curated_references", [])
    data_points = state.get("key_data_points", [])
    audience = state.get("target_audience", "泛科技读者")

    logger.info(f"📋 Outline: 生成大纲 (模式: {pattern})")

    try:
        llm = create_llm("outline")
        prompt_template = config.load_prompt("outline")

        refs_text = ""
        for i, ref in enumerate(references[:5], 1):
            refs_text += f"\n[{i}] {ref.get('title', '')} - {ref.get('source', '')}\n    {ref.get('snippet', '')}"

        data_text = "、".join(data_points[:8])

        user_prompt = prompt_template.replace("{title}", title)
        user_prompt = user_prompt.replace("{pattern}", pattern)
        user_prompt = user_prompt.replace("{references}", refs_text)
        user_prompt = user_prompt.replace("{data_points}", data_text)
        user_prompt = user_prompt.replace("{audience}", audience)

        messages = [SystemMessage(content=user_prompt), HumanMessage(content=f"请为主题「{title}」生成文章大纲。")]
        response = llm.invoke(messages)

        outline = parse_llm_json(
            response.content,
            expected_keys=["hook", "sections", "cta"],
        )

        sections = outline.get("sections", [])
        hook = outline.get("hook", {})
        cta = outline.get("cta", {})

        logger.info(f"✅ 大纲生成: hook={hook.get('type', 'N/A')}, {len(sections)} 个段落, cta={cta.get('type', 'N/A')}")

        return {"outline": outline}

    except Exception as e:
        logger.error(f"❌ Outline 失败: {e}")
        # 降级：简单大纲
        fallback_outline = {
            "hook": {"type": "question", "content": f"关于{title}，你了解多少？"},
            "sections": [
                {"heading": "背景", "key_points": ["行业现状"], "data_refs": [], "word_target": 300},
                {"heading": "核心解读", "key_points": ["关键分析"], "data_refs": [], "word_target": 500},
                {"heading": "影响与展望", "key_points": ["未来趋势"], "data_refs": [], "word_target": 300},
            ],
            "cta": {"type": "discussion", "content": "你怎么看？评论区聊聊"},
        }
        return {
            "outline": fallback_outline,
            "errors": [{"node": "outline", "error": str(e), "severity": "DEGRADABLE", "timestamp": ""}],
        }
