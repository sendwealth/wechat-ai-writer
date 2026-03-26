"""
LangGraph 工作流定义
"""
from langgraph.graph import StateGraph, END
from core.state import GlobalState
from core.nodes.search import search_tech_news_node
from core.nodes.extract import extract_topic_node
from core.nodes.deep_search import deep_search_node
from core.nodes.generate import generate_article_node
from core.nodes.images import generate_images_node
from core.nodes.layout import add_images_node
from core.nodes.publish import publish_to_wechat_node


def build_workflow():
    """构建工作流"""
    # 创建状态图（LangGraph 0.2.x API）
    builder = StateGraph(GlobalState)
    
    # 添加节点
    builder.add_node("search_tech_news", search_tech_news_node)
    builder.add_node("extract_topic", extract_topic_node)
    builder.add_node("deep_search", deep_search_node)
    builder.add_node("generate_article", generate_article_node)
    builder.add_node("generate_images", generate_images_node)
    builder.add_node("add_images", add_images_node)
    builder.add_node("publish_to_wechat", publish_to_wechat_node)
    
    # 设置入口点
    builder.set_entry_point("search_tech_news")
    
    # 添加边 - 线性流程
    builder.add_edge("search_tech_news", "extract_topic")
    builder.add_edge("extract_topic", "deep_search")
    builder.add_edge("deep_search", "generate_article")
    builder.add_edge("generate_article", "generate_images")
    builder.add_edge("generate_images", "add_images")
    builder.add_edge("add_images", "publish_to_wechat")
    builder.add_edge("publish_to_wechat", END)
    
    # 编译图
    return builder.compile()


# 导出主图
main_workflow = build_workflow()
