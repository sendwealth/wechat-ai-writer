"""
配置管理
"""
import os
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        
    def get_llm_config(self, config_name: str) -> Dict[str, Any]:
        """获取 LLM 配置"""
        config_path = self.config_dir / "llm" / f"{config_name}.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get_prompt(self, prompt_name: str) -> str:
        """获取提示词模板"""
        prompt_path = self.config_dir / "prompts" / f"{prompt_name}.txt"
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    @staticmethod
    def get_env(key: str, default: str = None) -> str:
        """获取环境变量"""
        return os.getenv(key, default)
    
    @staticmethod
    def get_llm_provider() -> str:
        """获取 LLM 提供商"""
        return os.getenv("LLM_PROVIDER", "doubao")
    
    @staticmethod
    def get_search_provider() -> str:
        """获取搜索提供商"""
        return os.getenv("SEARCH_PROVIDER", "serpapi")


# 全局配置实例
config = Config()
