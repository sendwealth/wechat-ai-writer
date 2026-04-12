"""
Agent: Editor - 针对性润色修改

输出格式：纯文本文章 + ---EDIT_NOTES--- 分隔 + JSON 修改说明
不再将完整文章包裹在 JSON 中，避免长文本截断。
"""
import json
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from llm import create_llm
from utils.config import config
from utils.logger import logger
from utils.json_parser import extract_json_text, repair_json


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

请根据以上反馈对文章进行针对性修改。"""

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)
        result_text = response.content.strip()

        # 解析分隔符格式：文章 + ---EDIT_NOTES--- + JSON
        separator = "---EDIT_NOTES---"
        edited = result_text
        notes = []

        if separator in result_text:
            parts = result_text.split(separator, 1)
            edited = parts[0].strip()

            if len(parts) > 1:
                notes_text = parts[1].strip()
                try:
                    notes_json = extract_json_text(notes_text)
                    notes = repair_json(notes_json)
                    # repair_json 返回 dict，notes 应该是 list
                    if isinstance(notes, dict):
                        notes = notes.get("edit_notes", notes.get("notes", [notes]))
                    elif not isinstance(notes, list):
                        notes = []
                except json.JSONDecodeError:
                    notes = [{"location": "全文", "change": "整体润色", "reason": "修改说明解析失败"}]
        else:
            # LLM 没用分隔符格式 — 整个输出当作文章
            # 尝试是否输出了 JSON 格式（兼容旧 prompt）
            if edited.startswith("{") and "edited_article" in edited:
                try:
                    parsed = repair_json(edited, expected_keys=["edited_article", "edit_notes"])
                    edited = parsed.get("edited_article", article)
                    notes = parsed.get("edit_notes", [])
                except json.JSONDecodeError:
                    pass  # 用原始文本

        # 日志 token 使用
        _log_token_usage(response, "editor")

        logger.info(f"✅ 编辑完成: {len(edited)} 字符, {len(notes)} 处修改")
        for note in notes[:3]:
            if isinstance(note, dict):
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
