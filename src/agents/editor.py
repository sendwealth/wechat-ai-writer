"""
Agent: Editor - 针对性润色修改
"""
import json
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from llm import create_llm
from utils.config import config
from utils.logger import logger


def editor_node(state: dict, run_config=None) -> dict:
    """根据 Critic 反馈做针对性修改"""
    article = state.get("draft_article", "")
    quality_scores = state.get("quality_scores", [])
    critic_feedback = state.get("critic_feedback", "")
    overall_score = state.get("overall_score", 0)

    logger.info(f"✏️ Editor: 润色文章 (原始分: {overall_score})")

    if not article:
        return {"edited_article": "", "edit_notes": []}

    try:
        llm = create_llm("editor")
        system_prompt = config.load_prompt("editor")

        # 格式化薄弱维度
        low_dims = [s for s in quality_scores if s.get("score", 10) < 8.0]
        dims_text = ""
        for s in low_dims:
            dims_text += f"\n- [{s.get('dimension', '')}] {s.get('score', 0)}/10: {s.get('feedback', '')}"

        user_prompt = f"""## 原始文章
{article}

## 评审总分: {overall_score}/10

## 薄弱维度（需要改进）:
{dims_text if dims_text else "整体良好，仅做轻微润色"}

## 总体反馈
{critic_feedback}

请根据以上反馈对文章进行针对性修改。输出JSON格式。"""

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)
        result_text = response.content.strip()

        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]

        try:
            result = json.loads(result_text.strip())
            edited = result.get("edited_article", article)
            notes = result.get("edit_notes", [])
        except json.JSONDecodeError:
            # LLM 有时直接返回文章而非 JSON
            edited = result_text
            notes = [{"location": "全文", "change": "整体润色", "reason": "JSON解析失败，使用原始返回"}]

        logger.info(f"✅ 编辑完成: {len(edited)} 字符, {len(notes)} 处修改")
        for note in notes[:3]:
            logger.info(f"   - {note.get('location', '')}: {note.get('change', '')}")

        return {
            "edited_article": edited,
            "edit_notes": notes,
        }

    except Exception as e:
        logger.error(f"❌ Editor 失败: {e}")
        return {
            "edited_article": article,  # 保持原稿
            "edit_notes": [],
            "errors": [{"node": "editor", "error": str(e), "severity": "DEGRADABLE", "timestamp": ""}],
        }
