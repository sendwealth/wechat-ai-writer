"""
节点2: 提取主题
"""
import json
import os
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import GlobalState
from llm import create_llm
from utils.config import config as app_config
from utils.logger import logger


def extract_topic_node(state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
    """
    提取文章主题
    
    Args:
        state: 全局状态
        config: 运行配置
    
    Returns:
        更新后的状态
    """
    logger.info("="*60)
    logger.info("🚀 节点2: 提取主题")
    logger.info("="*60)
    
    article = state.selected_article
    logger.info(f"📄 文章标题: {article.get('title', '未知')}")
    
    try:
        # 准备文章内容
        article_content = f"""
标题: {article.get('title', '')}
摘要: {article.get('snippet', '')}
来源: {article.get('source', '')}
        """.strip()
        
        # 加载 LLM 配置
        llm_config = app_config.get_llm_config("extract")
        
        # 创建 LLM
        llm = create_llm(llm_config)
        
        # 提示词
        sp = """你是内容策划专家，擅长从科技资讯中找到最有故事性的一个点。

你的任务：
从科技文章中找出**一个**最有故事性、最有价值的切入点，而不是概括所有内容。

核心原则：
1. **只选一个点**：不要试图覆盖所有方面
2. **聚焦具体场景**：主题要具体到某个场景、某个应用
3. **有故事性**：选的点要有具体的人物、事件、场景
4. **可深度展开**：这个点值得深入挖掘

输出格式（JSON）：
{
  "topic": "聚焦一个具体的、有故事性的点",
  "highlights": ["围绕这个点的3-5个具体细节或案例"]
}"""
        
        up = f"""请分析以下科技文章，找出**一个**最有故事性、最值得深入写的点：

{article_content}

要求：
- 主题要聚焦，不要大而全
- 只选一个最有故事的点
- 亮点要具体，不要抽象

请严格按照JSON格式输出。"""
        
        # 调用 LLM
        messages = [
            SystemMessage(content=sp),
            HumanMessage(content=up)
        ]
        
        response = llm.invoke(messages)
        result_text = response.content
        
        # 解析 JSON
        # 移除可能的 markdown 代码块标记
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]
        
        result = json.loads(result_text.strip())
        
        topic = result.get("topic", "")
        highlights = result.get("highlights", [])
        
        logger.info(f"✅ 提取主题: {topic}")
        logger.info(f"   亮点数量: {len(highlights)}")
        for i, h in enumerate(highlights, 1):
            logger.info(f"   {i}. {h[:50]}...")
        
        logger.info("="*60)
        logger.info("✅ 节点2完成")
        logger.info("="*60)
        
        return {
            "topic": topic,
            "highlights": highlights
        }
        
    except Exception as e:
        logger.error(f"❌ 主题提取失败: {e}")
        return {
            "topic": article.get('title', '未知主题'),
            "highlights": [article.get('snippet', '无亮点')]
        }
