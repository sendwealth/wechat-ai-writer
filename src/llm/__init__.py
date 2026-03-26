"""
LLM 工厂
"""
from typing import Dict, Any
from llm.base import BaseLLM
from llm.doubao import DoubaoLLM
from llm.openai import OpenAILLM
from llm.glm5 import GLM5LLM
from utils.config import config


def create_llm(llm_config: Dict[str, Any] = None) -> BaseLLM:
    """创建 LLM 实例"""
    provider = config.get_llm_provider()
    
    if provider == "doubao":
        return DoubaoLLM(llm_config)
    elif provider == "openai":
        return OpenAILLM(llm_config)
    elif provider == "glm" or provider == "zai" or provider == "glm5":
        return GLM5LLM(llm_config)
    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")
