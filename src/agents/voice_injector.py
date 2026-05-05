"""
Agent: Voice Injector - 生成个人视角胶囊，为文章注入「人味」
在 outline 完成后、writer 开始前执行
"""
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from llm import create_llm
from utils.config import config
from utils.logger import logger


# JTBD → 角色设定映射
JTBD_PERSONA = {
    "save_time": "一个每天都在关注AI动态但时间很紧的开发者，你帮别人筛选信息，说话直接、挑重点",
    "learn_skill": "一个喜欢亲手尝试各种AI工具的极客，踩坑无数但乐在其中，有一说一",
    "social_currency": "一个对AI行业有自己判断的观察者，不怕说错，经常有反常识的观点",
    "resonance": "一个和你一样的普通技术人，在AI浪潮里有焦虑也有兴奋，说话接地气",
}

JTBD_VOICE_STYLE = {
    "save_time": "短句为主、直击要点、不要铺垫、像发朋友圈一样干脆",
    "learn_skill": "步骤感强、有细节、有对比、像同事演示给你看",
    "social_currency": "有态度、敢下判断、引数据、像饭局上的犀利发言",
    "resonance": "真实坦白、不说教、像深夜聊天的朋友",
}


def voice_injector_node(state: dict, run_config=None) -> dict:
    """生成个人视角胶囊，注入 writer 提供「人味锚点」"""
    topic = state.get("topic_keyword", "科技")
    jtbd = state.get("jtbd", "learn_skill")
    outline = state.get("outline", {})
    title = state.get("selected_title", topic)

    logger.info(f"🎙️ Voice Injector: 为 '{title}' 生成个人视角 (JTBD: {jtbd})")

    try:
        llm = create_llm("voice_injector")

        persona = JTBD_PERSONA.get(jtbd, JTBD_PERSONA["learn_skill"])
        style = JTBD_VOICE_STYLE.get(jtbd, JTBD_VOICE_STYLE["learn_skill"])

        system_prompt = f"""你是一个真实的人，不是AI。你的角色是：{persona}

请根据下面的文章主题，写一段你的「真实体验和感受」（200-300字）。

要求：
1. 用第一人称「我」，像一个真人在分享
2. 表述风格：{style}
3. 必须包含：
   - 一个具体的场景（什么情况下接触/使用/思考这个话题的）
   - 一个具体的数字或细节（不是概括性描述）
   - 一个你个人的判断（可以正面也可以负面，但不能说「有利有弊」这种废话）
   - 至少一处犹豫/保留/自嘲（「也可能是我没搞懂」「说实话我也不确定」）
4. 禁止：
   - 「在当今...的时代」「随着...的发展」「综上所述」「不可否认」
   - 「首先/其次/最后」
   - 任何万能句式
5. 像跟朋友发微信一样自然，不要写成报告"""

        user_prompt = f"""文章标题：{title}
文章主题：{topic}

请以你的角色视角，写一段关于这个话题的真实体验和感受。

开头给你参考（你可以完全不用，用自己的方式）：
- 「上周我...」（时间+事件）
- 「说实话，我第一次...」（坦白）
- 「我试了XX之后发现...」（体验）
- 「很多人觉得...但我自己的感受是...」（观点）

只输出你的个人体验描述，不要标题、不要署名、不要任何格式标记。"""

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = llm.invoke(messages)
        voice_capsule = response.content.strip()

        # 日志
        _log_token_usage(response, "voice_injector")
        logger.info(f"✅ 个人视角胶囊生成: {len(voice_capsule)} 字符")
        logger.info(f"   前80字: {voice_capsule[:80]}...")

        return {"voice_capsule": voice_capsule}

    except Exception as e:
        logger.error(f"❌ Voice Injector 失败: {e}")
        # 降级：返回一个通用的人味提示
        fallback = f"作为一个经常关注{topic}的人，我有一些真实的感受和想法想要分享。"
        return {
            "voice_capsule": fallback,
            "errors": [{"node": "voice_injector", "error": str(e), "severity": "DEGRADABLE", "timestamp": ""}],
        }


def _log_token_usage(response, agent_name: str):
    """记录 LLM 响应的 token 使用量"""
    try:
        meta = getattr(response, 'response_metadata', {}) or {}
        token_usage = meta.get('token_usage', {}) or meta.get('usage', {}) or {}
        prompt_tokens = token_usage.get('prompt_tokens', 0)
        completion_tokens = token_usage.get('completion_tokens', 0)
        total = token_usage.get('total_tokens', prompt_tokens + completion_tokens)

        if completion_tokens > 0:
            logger.info(f"   📊 [{agent_name}] tokens: prompt={prompt_tokens}, completion={completion_tokens}, total={total}")
    except Exception:
        pass
