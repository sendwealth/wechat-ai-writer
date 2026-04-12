"""
统一 OpenAI 兼容 LLM 客户端
合并原有的 GLM5LLM / OpenAILLM / DoubaoLLM 三个类
"""
import time
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

    def invoke(self, messages, max_retries: int = 3, base_delay: float = 2.0):
        """调用 LLM，自动重试 429/500 错误

        Args:
            messages: LangChain 消息列表
            max_retries: 最大重试次数
            base_delay: 首次重试等待秒数（指数退避）
        """
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = self._llm.invoke(messages)
                return response
            except Exception as e:
                error_str = str(e)
                is_retryable = (
                    "429" in error_str
                    or "rate" in error_str.lower()
                    or "500" in error_str
                    or "502" in error_str
                    or "503" in error_str
                    or "timeout" in error_str.lower()
                )

                if is_retryable and attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"⚠️ LLM[{self.agent_name}] 第{attempt+1}次失败: "
                        f"{error_str[:80]}，{delay:.1f}s 后重试..."
                    )
                    time.sleep(delay)
                    last_error = e
                else:
                    raise

        raise last_error


def create_llm(agent_name: str = "writer") -> UnifiedLLM:
    """工厂函数：创建 LLM 实例"""
    return UnifiedLLM(agent_name=agent_name)
