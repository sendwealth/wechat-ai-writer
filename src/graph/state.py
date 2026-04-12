"""
WorkflowState - 分层解耦的状态定义
替代原有的 GlobalState God Object
"""
from typing import TypedDict, Annotated
from operator import add


class ErrorRecord(TypedDict):
    """错误记录"""
    node: str
    error: str
    severity: str  # FATAL / RETRYABLE / DEGRADABLE
    timestamp: str


class QualityScore(TypedDict):
    """单维度质量评分"""
    dimension: str  # hook / structure / persuasiveness / readability / originality / cta
    score: float    # 0-10
    feedback: str


class WorkflowState(TypedDict):
    """多 Agent 工作流全局状态"""
    # ── 输入 ──
    topic_keyword: str
    dry_run: bool

    # ── Orchestrator 输出 ──
    topic_category: str          # ai_tools / tech_trends / career / lifestyle
    article_pattern: str         # conflict / listicle / story / essay
    target_audience: str         # 程序员 / 职场人 / 创业者 / 泛科技读者
    writing_strategy: dict       # 写作策略参数

    # ── Research Agent ──
    search_results: list         # 原始搜索结果
    curated_references: list     # 筛选后的参考资料
    key_data_points: list        # 提取的关键数据点

    # ── Title Generator ──
    title_candidates: list       # [{title, strategy, rule_score, llm_score, final_score}]
    selected_title: str
    title_score: float

    # ── Outline Agent ──
    outline: dict                # {hook, sections, cta}

    # ── Writer Agent ──
    draft_article: str
    write_round: int             # 当前写作轮次
    score_history: list          # 每轮 overall_score 记录，用于提前退出

    # ── Critic Agent ──
    quality_scores: list         # [QualityScore, ...]
    overall_score: float
    critic_feedback: str

    # ── Editor Agent ──
    edited_article: str
    edit_notes: list

    # ── Visual Agent ──
    image_plan: list             # [{position, prompt, alt_text}]
    article_images: list         # [{url, wechat_url, alt}]

    # ── Layout Agent ──
    article_html: str

    # ── Publisher Agent ──
    publish_result: dict
    publish_success: bool

    # ── 全局控制 ──
    regroup_round: int           # 降级重做轮次
    errors: Annotated[list, add] # 累积错误（追加，不覆盖）
