"""
统一 OpenAI 兼容 LLM 客户端
合并原有的 GLM5LLM / OpenAILLM / DoubaoLLM 三个类
"""
from langchain_openai import ChatOpenAI
from utils.config import config
from utils.logger import logger


class UnifiedLLM:
    """统一的 OpenAI 兼容 LLM 客户端"""

    def __init__(self, agent_name: str = "writer"):
        """
        根据agent名称加载对应配置

        Args:
            agent_name: agent名称，用于从settings.yaml读取参数
        """
        self.agent_name = agent_name
        self._llm = self._build()

    def _build(self) -> ChatOpenAI:
        """构建 ChatOpenAI 实例"""
        llm_config = config.get_llm_config()
        agent_config = config.get_agent_config(self.agent_name)

        api_key = llm_config["api_key"]
        base_url = llm_config["base_url"]
        model = agent_config.get("model", llm_config.get("model", "glm-5"))
        temperature = agent_config.get("temperature", 0.7)
        max_tokens = agent_config.get("max_tokens", 4000)

        logger.debug(
            f"LLM[{self.agent_name}]: model={model}, "
            f"temp={temperature}, max_tokens={max_tokens}"
        )

        return ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @property
    def llm(self) -> ChatOpenAI:
        """获取底层 ChatOpenAI 实例"""
        return self._llm

    def invoke(self, messages):
        """调用 LLM"""
        return self._llm.invoke(messages)


def create_llm(agent_name: str = "writer") -> UnifiedLLM:
    """工厂函数：创建 LLM 实例"""
    return UnifiedLLM(agent_name=agent_name)
