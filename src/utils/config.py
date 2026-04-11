"""
配置管理 - 基于 YAML 的统一配置
环境变量 (.env) 仅存密钥，其他配置走 settings.yaml
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """统一配置管理器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        self._settings: Dict[str, Any] = {}
        self._load_settings()

    def _load_settings(self):
        """加载 settings.yaml"""
        settings_path = self.config_dir / "settings.yaml"
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                self._settings = yaml.safe_load(f) or {}

    def get(self, dotpath: str, default: Any = None) -> Any:
        """
        点号路径获取配置
        例: config.get("workflow.max_write_rounds") → 5
        """
        keys = dotpath.split('.')
        value = self._settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """获取某个 Agent 的配置"""
        return self.get(f"agents.{agent_name}", {})

    def get_llm_config(self) -> Dict[str, Any]:
        """获取当前 LLM 提供商配置"""
        provider = os.getenv("LLM_PROVIDER") or self.get("llm.provider", "glm")
        provider_config = self.get(f"llm.{provider}", {})
        # 从环境变量读取 API Key
        api_key_env = provider_config.get("api_key_env", "")
        api_key = os.getenv(api_key_env, "")
        return {
            "provider": provider,
            "api_key": api_key,
            "base_url": provider_config.get("base_url", ""),
            "model": provider_config.get("model", "glm-5"),
        }

    def load_prompt(self, prompt_name: str) -> str:
        """从 config/prompts/ 加载提示词模板"""
        prompt_path = self.config_dir / "prompts" / f"{prompt_name}.md"
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        return ""

    @staticmethod
    def get_env(key: str, default: str = None) -> str:
        """获取环境变量"""
        return os.getenv(key, default)


# 全局配置实例
config = Config()
