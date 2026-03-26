"""
GLM-5 LLM 集成（智谱AI）
"""
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from llm.base import BaseLLM
from utils.config import config


class GLM5LLM(BaseLLM):
    """GLM-5 LLM（智谱AI）"""
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        super().__init__(llm_config)
        self.api_key = config.get_env("ZAI_API_KEY") or config.get_env("OPENAI_API_KEY")
        self.base_url = config.get_env("ZAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        
        if not self.api_key:
            raise ValueError("ZAI_API_KEY 或 OPENAI_API_KEY 未配置")
    
    def build(self) -> ChatOpenAI:
        """构建 GLM-5 LLM 实例"""
        model = self.config.get("model", "glm-5")
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
