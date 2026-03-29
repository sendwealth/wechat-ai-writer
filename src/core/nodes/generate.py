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
    生成公众号文章（爆款结构）
    
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
        
        # 加载爆款文章模板
        prompt_path = Path(__file__).parent.parent.parent / "config" / "prompts" / "article_template_v2.md"
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                base_prompt = f.read()
        except Exception as e:
            logger.error(f"⚠️ 加载文章模板失败: {e}")
            base_prompt = "生成一篇高质量文章"
        
        # 加载 LLM 配置
        llm_config = app_config.get_llm_config("generate")
        
        # 创建 LLM
        llm = create_llm(llm_config)
        
        # 提示词（爆款结构）
        sp = f"""{base_prompt}

<<<<<<< HEAD
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
=======
**当前任务**：
主题：{topic}

核心亮点：
>>>>>>> d4a6cab (feat: 完整优化方案 - Phase 1 内容质量优化)
{highlights_text}

参考资料：
{reference_content}

**生成要求**：
- 字数：2000-3000字
- 结构：暴力破题 → 痛点共鸣 → 价值交付 → 互动引导 → 行动召唤
- 语气：实用、友好、真实
- 融入个人视角（真实案例/体验）
- 适当使用emoji（增加趣味性）
- 每段不超过3行（提高可读性）
- 关键信息加粗（突出重点）

直接输出文章内容
不要任何开场白或结束语。"""
        
        up = f"请根据以上要求，生成一篇关于「{topic}」的微信公众号文章。"
        
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
