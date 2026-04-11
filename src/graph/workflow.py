"""
LangGraph 工作流定义 - 多 Agent 协作图
包含条件边、并行分支、质量关卡
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from graph.state import WorkflowState
from graph.routers import route_after_critic, route_final

from agents.orchestrator import orchestrator_node
from agents.research import research_node
from agents.title_generator import title_generator_node
from agents.outline import outline_node
from agents.writer import writer_node
from agents.critic import critic_node
from agents.editor import editor_node
from agents.visual import visual_node
from agents.layout import layout_node
from agents.publisher import publisher_node

from utils.config import config
from utils.logger import logger


def _regroup_node(state: dict, run_config=None) -> dict:
    """降级重做：换文章结构模式，回到 Orchestrator"""
    import random
    patterns = ["conflict", "listicle", "story", "essay"]
    current = state.get("article_pattern", "essay")
    remaining = [p for p in patterns if p != current]
    new_pattern = random.choice(remaining) if remaining else "essay"

    regroup_round = state.get("regroup_round", 0) + 1
    logger.info(f"🔄 降级重做 #{regroup_round}: {current} → {new_pattern}")

    return {
        "article_pattern": new_pattern,
        "regroup_round": regroup_round,
        "write_round": 0,
    }


def _final_check_node(state: dict, run_config=None) -> dict:
    """质量终审：检查分数和错误，决定是否发布"""
    overall_score = state.get("overall_score", 0)
    errors = state.get("errors", [])
    final_threshold = config.get("workflow.final_threshold", 7.0)

    fatal_errors = [e for e in errors if e.get("severity") == "FATAL"]

    logger.info(f"⚖️ 终审: 分数 {overall_score}, 致命错误 {len(fatal_errors)}")

    # 状态透传（路由函数读取 state 做决策）
    return {}


def build_workflow():
    """构建多 Agent 工作流"""
    builder = StateGraph(WorkflowState)

    # ── 添加节点 ──
    builder.add_node("orchestrator",    orchestrator_node)
    builder.add_node("research",        research_node)
    builder.add_node("title_generator", title_generator_node)
    builder.add_node("create_outline",  outline_node)
    builder.add_node("writer",          writer_node)
    builder.add_node("critic",          critic_node)
    builder.add_node("editor",          editor_node)
    builder.add_node("visual",          visual_node)
    builder.add_node("layout",          layout_node)
    builder.add_node("final_check",     _final_check_node)
    builder.add_node("publisher",       publisher_node)
    builder.add_node("regroup",         _regroup_node)

    # ── 入口 ──
    builder.set_entry_point("orchestrator")

    # ── 并行分支：研究和标题生成同时启动 ──
    builder.add_edge("orchestrator", "research")
    builder.add_edge("orchestrator", "title_generator")

    # ── 汇合后生成大纲 ──
    builder.add_edge("research", "create_outline")
    builder.add_edge("title_generator", "create_outline")

    # ── 写作 → 评审 ──
    builder.add_edge("create_outline", "writer")
    builder.add_edge("writer", "critic")

    # ── Critic 条件边 ──
    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "editor":  "editor",
            "rewrite": "writer",
        }
    )

    # ── Editor → Visual → Layout → 终审 ──
    builder.add_edge("editor", "visual")
    builder.add_edge("visual", "layout")
    builder.add_edge("layout", "final_check")

    # ── 终审条件边 ──
    builder.add_conditional_edges(
        "final_check",
        route_final,
        {
            "publish":  "publisher",
            "regroup":  "regroup",
        }
    )

    # ── 降级重做回到 Orchestrator ──
    builder.add_edge("regroup", "orchestrator")

    # ── 发布结束 ──
    builder.add_edge("publisher", END)

    # ── 编译 ──
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    return graph


# 导出主图
main_workflow = build_workflow()
