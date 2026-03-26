"""
豆包 LLM 集成
"""
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from llm.base import BaseLLM
from utils.config import config


class DoubaoLLM(BaseLLM):
    """豆包 LLM"""
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        super().__init__(llm_config)
        self.api_key = config.get_env("DOUBAO_API_KEY")
        self.base_url = config.get_env("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        
        if not self.api_key:
            raise ValueError("DOUBAO_API_KEY 未配置")
    
    def build(self) -> ChatOpenAI:
        """构建豆包 LLM 实例"""
        model = self.config.get("model", "doubao-seed-1-6-251015")
        temperature = self.config.get("temperature", 0.7)
        max_tokens = self.config.get("max_tokens", 2000)
        top_p = self.config.get("top_p", 0.9)
        
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            api_key=self.api_key,
            base_url=self.base_url
        )
