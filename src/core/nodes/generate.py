"""
节点4: 生成文章
"""
from typing import Dict, Any
from pathlib import Path
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import GlobalState
from llm import create_llm
from utils.config import config as app_config
from utils.logger import logger


def generate_article_node(state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
    """
    生成公众号文章（基于真实新闻）
    
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
        
        # 提示词（基于真实新闻）
        sp = """你是一位专业的科技新闻编辑，擅长撰写深度解读文章。

**核心原则**：
1. 基于事实：只使用参考资料中的真实信息，严禁虚构
2. 客观专业：使用第三人称叙述，不要虚构第一人称故事
3. 深度分析：解读技术趋势、行业影响、未来展望
4. 通俗易懂：用简单语言解释复杂技术

**内容要求**：
- 必须基于提供的参考资料撰写，不得编造数据、案例或人物
- 引用数据、观点时要标注来源（如"据XX报道"、"XX数据显示"）
- 可以对已知事实进行合理推断，但要明确说明是推测
- 保持客观中立，避免过度主观评价

**排版格式（微信公众号适配）**：
- 标题：单独一行，居中
- 小标题：单独一行，前后各空一行
- 正文：每段3-5句话，段落间空一行
- 重点：可用【】或「」标注，不要用**加粗**
- 列表：用①②③或•符号，每项单独一行
- 禁止使用Markdown格式（#、**、###等）

**文章结构**：
- 开头：概括核心事件/趋势（100-200字）
- 背景：相关技术/行业发展现状（300-500字）
- 解读：深入分析核心亮点（500-800字）
- 影响：对行业/用户的意义（300-500字）
- 展望：未来发展趋势（200-300字）
- 结尾：总结要点（100字）

**语言风格**：
- 专业但不晦涩
- 亲切但不说教
- 深入但不冗长

请直接输出文章内容，不要任何开场白。"""
        
        up = f"""主题：{topic}

核心亮点：
{highlights_text}

参考资料：
{reference_content}

请基于以上资料，撰写一篇关于「{topic}」的深度解读文章。要求：
1. 只使用资料中的真实信息
2. 使用客观、专业的叙述方式
3. 符合微信公众号排版格式
4. 字数1500-2000字

直接输出文章内容。"""
        
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
            "article": f"{topic}\n\n生成失败，请重试。"
        }
