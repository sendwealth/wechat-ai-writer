"""
节点4: 生成文章
"""
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import GlobalState
from llm import create_llm
from utils.config import config as app_config
from utils.logger import logger


def generate_article_node(state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
    """
    生成公众号文章
    
    Args:
        state: 全局状态
        config: 运行配置（LangGraph 传入，未使用）
    
    Returns:
        更新后的状态
    """
    logger.info("="*60)
    logger.info("🚀 节点4: 生成文章")
    logger.info("="*60)
    
    topic = state.topic
    highlights = state.highlights
    deep_results = state.deep_search_results
    
    logger.info(f"📝 文章主题: {topic}")
    logger.info(f"   亮点数量: {len(highlights)}")
    logger.info(f"   参考资料: {len(deep_results)}")
    
    try:
        # 整理参考资料
        reference_content = ""
        for idx, result in enumerate(deep_results[:5], 1):
            reference_content += f"\n参考{idx}: {result['title']}\n{result['snippet']}\n"
        
        highlights_text = "\n".join([f"- {h}" for h in highlights[:5]])
        
        # 加载 LLM 配置
        llm_config = app_config.get_llm_config("generate")
        
        # 创建 LLM
        llm = create_llm(llm_config)
        
        # 提示词
        sp = """你就是一个普通人，写文章像和朋友聊天，但是你要专注讲好一个故事。

核心原则：
1. **聚焦一个点，深入挖掘**：整篇文章只围绕一个主题展开
2. **故事驱动，细节为王**：
   - 开头用一个具体的场景切入
   - 深入展开这个场景，包括背景、过程、细节
   - 有具体的人物、对话、感受
3. **深入挖掘，不要泛泛而谈**
4. **自然延伸，点到为止**
5. **语言风格要求**：
   - 彻底去掉官腔和AI味
   - 用最生活化的语言
   - 多用"我"、"你"，少用"人们"、"大家"
6. **排版要求（重要！）**：
   - 每段 2-3 句话，不超过 100 字
   - 段落之间用空行分隔
   - 适当使用小标题（###）分隔不同部分
   - 避免大段文字堆砌

文章结构：
- 第1段：用一个具体的场景切入（短段落）
- 第2-3段：深入讲述背景、过程、细节（分段呈现）
- 第4-5段：带来的变化、意义（用小标题分隔）
- 最后：自然引申出一点思考（独立段落）

严禁：
- 提多个不同的应用场景
- 列举多个案例
- 面面俱到地介绍
- 写超过 100 字的长段落

请直接输出文章内容，不要任何开场白。注意排版美观！"""
        
        up = f"""主题：{topic}

核心细节：
{highlights_text}

参考资料（背景信息）：
{reference_content}

要求：
- 整篇文章只围绕这个主题展开
- 深入挖掘一个故事，不要泛泛而谈
- 有具体的场景、人物、细节
- 自然、生活化，像一个真人在写"""
        
        # 调用 LLM
        messages = [
            SystemMessage(content=sp),
            HumanMessage(content=up)
        ]
        
        response = llm.invoke(messages)
        article = response.content
        
        logger.info(f"✅ 生成文章成功")
        logger.info(f"   文章长度: {len(article)} 字符")
        logger.info(f"   文章预览: {article[:100]}...")
        
        logger.info("="*60)
        logger.info("✅ 节点4完成")
        logger.info("="*60)
        
        return {
            "article": article
        }
        
    except Exception as e:
        logger.error(f"❌ 文章生成失败: {e}")
        return {
            "article": f"# {topic}\n\n生成失败，请重试。"
        }
