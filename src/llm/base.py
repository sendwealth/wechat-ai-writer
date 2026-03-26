"""
LLM 基础类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_core.language_models import BaseChatModel


class BaseLLM(ABC):
    """LLM 基础类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.llm = None
    
    @abstractmethod
    def build(self) -> BaseChatModel:
        """构建 LLM 实例"""
        pass
    
    def invoke(self, prompt: str, **kwargs):
        """调用 LLM"""
        if not self.llm:
            self.llm = self.build()
        return self.llm.invoke(prompt, **kwargs)
    
    async def ainvoke(self, prompt: str, **kwargs):
        """异步调用 LLM"""
        if not self.llm:
            self.llm = self.build()
        return await self.llm.ainvoke(prompt, **kwargs)
