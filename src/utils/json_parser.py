"""
统一 LLM JSON 输出解析器

解决三个问题：
1. LLM 输出被 markdown code block 包裹 (```json ... ```)
2. LLM 输出被 max_tokens 截断 (Unterminated string)
3. LLM 偶尔输出非 JSON 文本
"""
import json
import re
from typing import Any, Dict, List, Optional, Union
from utils.logger import logger


def extract_json_text(raw: str) -> str:
    """从 LLM 原始输出中提取 JSON 文本。

    处理的情况：
    - 纯 JSON
    - ```json ... ``` 包裹
    - ``` ... ``` 包裹
    - JSON 前后有文字说明
    """
    text = raw.strip()

    # 尝试提取 code block
    if "```json" in text:
        parts = text.split("```json")
        if len(parts) > 1:
            inner = parts[1]
            if "```" in inner:
                text = inner.split("```")[0].strip()
            else:
                # code block 没闭合 — 截断场景
                text = inner.strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) > 1:
            inner = parts[1]
            if "```" in inner:
                text = inner.split("```")[0].strip()
            else:
                text = inner.strip()

    return text.strip()


def _truncate_unterminated_string(text: str) -> str:
    """处理 JSON 中未闭合的字符串。

    找到最后一个未配对的 "，截断到它之前，闭合当前字符串。
    """
    # 找到最后一个完整的 JSON value 结束位置
    # 策略：从后往前找，跳过尾部空白后找到有意义的截断点

    # 情况1: 截断在字符串值中间 — 最后一个非空白字符不是 } ] , : "
    # 需要找到最后一个 " 开始的字符串并闭合它

    in_string = False
    escape_next = False
    last_quote_pos = -1

    for i, ch in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\':
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            if in_string:
                last_quote_pos = i

    if in_string:
        # 有未闭合的字符串
        # 从 last_quote_pos 开始，截取到某个合理的位置
        # 简单策略：在 last_quote_pos 之后找一个句号/逗号/换行作为截断点
        remainder = text[last_quote_pos + 1:]
        # 找最后一个中文句号、句号、感叹号、换行作为截断点
        cut_chars = ['。', '，', '、', '\n', '.', ',', '！', '？', '；']
        cut_pos = -1
        for ch in cut_chars:
            pos = remainder.rfind(ch)
            if pos > cut_pos:
                cut_pos = pos

        if cut_pos > 0:
            # 截断到这个位置，闭合字符串
            truncated = text[:last_quote_pos + 1 + cut_pos + 1] + '"'
        else:
            # 找不到好的截断点，直接在 last_quote_pos 后闭合空字符串
            truncated = text[:last_quote_pos + 1] + '"'
        return truncated

    return text


def _close_brackets(text: str) -> str:
    """补全未闭合的 [] 和 {}。"""
    stack = []
    in_string = False
    escape_next = False

    for ch in text:
        if escape_next:
            escape_next = False
            continue
        if ch == '\\':
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in '{[':
            stack.append(ch)
        elif ch == '}' and stack and stack[-1] == '{':
            stack.pop()
        elif ch == ']' and stack and stack[-1] == '[':
            stack.pop()

    # 反向补全
    for bracket in reversed(stack):
        if bracket == '{':
            text += '}'
        elif bracket == '[':
            text += ']'

    return text


def repair_json(text: str, expected_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """修复并解析可能被截断的 LLM JSON 输出。

    三层修复策略：
    1. 直接解析
    2. 截断未闭合字符串 + 补全括号
    3. 正则提取关键字段（兜底）

    Args:
        text: LLM 输出的原始文本（应先通过 extract_json_text 处理）
        expected_keys: 期望的 JSON key 列表，用于正则兜底提取

    Returns:
        解析后的 dict

    Raises:
        json.JSONDecodeError: 所有修复策略都失败时
    """
    # 策略 1: 直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 策略 2: 修复截断
    try:
        fixed = _truncate_unterminated_string(text)
        fixed = _close_brackets(fixed)
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # 策略 3: 回退搜索 — 找到文本中第一个能解析的 JSON 对象
    # 尝试不同长度的前缀（从第一个 { 到最后一个 }）
    first_brace = text.find('{')
    if first_brace >= 0:
        for i in range(len(text) - 1, first_brace, -1):
            if text[i] == '}':
                try:
                    candidate = text[first_brace:i + 1]
                    fixed = _truncate_unterminated_string(candidate)
                    fixed = _close_brackets(fixed)
                    return json.loads(fixed)
                except json.JSONDecodeError:
                    continue

    # 策略 4: 正则提取（最后手段）
    if expected_keys:
        result = {}
        for key in expected_keys:
            # 匹配 "key": "string_value" 或 "key": number
            str_match = re.search(rf'"{re.escape(key)}"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
            if str_match:
                result[key] = str_match.group(1)
                continue
            num_match = re.search(rf'"{re.escape(key)}"\s*:\s*(\d+\.?\d*)', text)
            if num_match:
                val = num_match.group(1)
                result[key] = float(val) if '.' in val else int(val)

        if result:
            logger.warning(f"⚠️ JSON 修复失败，正则提取到 {len(result)} 个字段: {list(result.keys())}")
            return result

    raise json.JSONDecodeError("无法修复 JSON", text, 0)


def parse_llm_json(raw: str, expected_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """一站式解析 LLM JSON 输出。

    extract_json_text → repair_json 的组合。

    Args:
        raw: LLM 的 response.content 原始文本
        expected_keys: 期望的 JSON key，用于兜底正则提取

    Returns:
        解析后的 dict
    """
    text = extract_json_text(raw)
    return repair_json(text, expected_keys=expected_keys)
