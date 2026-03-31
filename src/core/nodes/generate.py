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
        # 整理参考资料（包含来源和URL）
        reference_content = ""
        for idx, result in enumerate(deep_results[:5], 1):
            reference_content += f"\n参考{idx}:\n来源：{result['source']}\n标题：{result['title']}\n链接：{result['url']}\n摘要：{result['snippet']}\n"
        
        highlights_text = "\n".join([f"- {h}" for h in highlights[:5]])
        
        # 加载 LLM 配置
        llm_config = app_config.get_llm_config("generate")
        
        # 创建 LLM
        llm = create_llm(llm_config)
        
        # 提示词（时效性+说服力+引用来源）
        sp = """你是一位资深的科技新闻深度解读作者，擅长撰写具有说服力的微信公众号文章。

**核心原则**：
1. **时效性优先** - 强调新闻的时效性，使用"近日"、"本周"、"最新"等词汇，开头点明时间背景
2. **真实性第一** - 只使用参考资料中明确提到的信息，不编造数据
3. **引用来源** - 每个数据和观点都要标注来源（如"据新华网报道"、"IBM数据显示"）
4. **说服力强** - 使用具体数字、百分比、统计数据、真实案例支撑观点

**内容要求**：
- 开头必须强调时效性："近日..."、"本周..."、"最新消息显示..."
- 引用数据时必须标注来源："据XX数据显示，...增长30%"、"XX报告指出，..."
- 使用具体案例："以XX为例，..."、"以XX公司的实践来看，..."
- 对比分析："相比去年，..."、"与XX相比，..."
- 避免模糊表述："有数据显示"→"据[具体来源]数据显示"

**说服力要素**：
- 具体数字：不说"大幅增长"，说"增长30%"
- 具体时间：不说"最近"，说"2026年3月"
- 具体来源：不说"有报告"，说"据IBM 2026 AI趋势报告"
- 具体案例：引用真实公司、产品、事件

**排版格式（微信公众号适配）**：
- 标题：单独一行，居中
- 小标题：单独一行，前后各空一行
- 正文：每段3-5句话，段落间空一行
- 重点：可用【】或「」标注，不要用**加粗**
- 列表：用①②③或•符号，每项单独一行
- 禁止使用Markdown格式（#、**、###等）

**文章结构**：
- 开头：强调时效性+概括核心事件（100-200字）
- 背景：相关技术/行业发展现状，引用数据（300-500字）
- 解读：深入分析核心亮点，使用案例（500-800字）
- 影响：对行业/用户的意义，引用统计数据（300-500字）
- 展望：未来发展趋势，引用专家观点（200-300字）
- 结尾：总结要点（100字）

**语言风格**：
- 专业但不晦涩
- 亲切但不说教
- 深入但不冗长

请直接输出文章内容，不要任何开场白。"""
        
        up = f"""主题：{topic}

核心亮点：
{highlights_text}

参考资料（包含来源）：
{reference_content}

请基于以上资料，撰写一篇关于「{topic}」的深度解读文章。要求：
1. **时效性优先** - 开头强调"近日"、"本周"等时效性，让读者感受到新闻的新鲜度
2. **真实性** - 只使用资料中的真实信息，不编造数据
3. **引用来源** - 每个数据和观点都要标注来源（如"据新华网报道"、"IBM数据显示"）
4. **说服力** - 使用具体数字、百分比、统计数据、真实案例支撑观点
5. **专业格式** - 符合微信公众号排版格式，不使用Markdown
6. **字数要求** - 1500-2000字

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
