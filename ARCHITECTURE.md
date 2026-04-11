# 多 Agent 微信公众号 AI 写作系统 — 架构设计

> 版本: 2.0 | 基于 LangGraph 多 Agent 架构 | 2026-04-11

---

## 一、设计目标

将当前 7 步线性管道升级为 **多 Agent 协作系统**，核心目标：

1. **文章质量**：通过 Critic-Editor 循环迭代，多维度评分驱动质量提升
2. **标题优化**：生成多个候选标题，LLM 评分 + 规则评分加权选择
3. **结构多样**：根据主题类型自动选择文章结构模式（冲突递进/清单体/故事驱动/总分总）
4. **可控性强**：质量阈值可配，低于阈值自动循环优化，直到达标
5. **容错可靠**：错误不掩盖，失败不发布；关键步骤可重试；全程无人值守

---

## 二、系统架构总览

```
                          ┌──────────────┐
                          │   用户输入    │
                          │ keyword/topic │
                          └──────┬───────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Orchestrator (路由)    │
                    │  主题分类 → 选择写作策略  │
                    └────┬──────────┬─────────┘
                         │          │
              ┌──────────▼──┐  ┌───▼───────────┐
              │ Research    │  │ Title         │  ← 并行
              │ Agent       │  │ Generator     │
              │ (搜索+筛选) │  │ (多标题生成)   │
              └──────┬──────┘  └───────┬───────┘
                     │                 │
              ┌──────▼─────────────────▼──────┐
              │         Outline Agent          │
              │    (大纲生成 + 结构选择)        │
              └──────────────┬────────────────┘
                             │
                  ┌──────────▼──────────┐
                  │     Writer Agent     │ ◄─────────────────┐
                  │  (分节写作+风格控制)  │                   │
                  └──────────┬──────────┘                   │
                             │                              │
                  ┌──────────▼──────────┐                   │
                  │    Critic Agent      │                   │
                  │   (多维质量评分)      │                   │
                  └──────┬───────┬───────┘                   │
                         │       │                           │
               score ≥  │       │ score <                   │
               7.5       │       │ 7.5                       │
                         │       │                           │
                  ┌──────▼──┐ ┌──▼──────────────────────────┘
                  │ Editor  │ │ 返回 Writer（反馈注入 Prompt）
                  │ Agent   │ │ 最多 5 轮，每轮逐步降低温度
                  └────┬────┘ └───────────────────────────►
                       │
              ┌────────▼─────────────────────┐
              │       Visual Agent            │
              │  (配图规划 + 生成 + 微信上传)  │
              └──────────────┬────────────────┘
                             │
              ┌──────────────▼────────────────┐
              │    Layout Agent                │
              │  (微信公众号 HTML 排版)         │
              └──────────────┬────────────────┘
                             │
                    ┌────────▼────────┐
                    │  质量终审        │
                    │  (final_check)   │
                    └──┬─────────┬────┘
                       │         │
                 pass  │         │ fail
                       │         │
              ┌────────▼───┐ ┌───▼────────────────┐
              │ Publisher  │ │ 返回 Writer         │
              │ Agent      │ │ (降级策略：换结构重写)│
              └────────────┘ └────────────────────►
```

---

## 三、Graph 拓扑设计（LangGraph StateGraph）

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

builder = StateGraph(WorkflowState)

# === 节点 ===
builder.add_node("orchestrator",      orchestrator_node)
builder.add_node("research",          research_node)
builder.add_node("title_generator",   title_generator_node)
builder.add_node("outline",           outline_node)
builder.add_node("writer",            writer_node)
builder.add_node("critic",            critic_node)
builder.add_node("editor",            editor_node)
builder.add_node("visual",            visual_node)
builder.add_node("layout",            layout_node)
builder.add_node("final_check",       final_check_node)
builder.add_node("publisher",         publisher_node)

# === 入口 ===
builder.set_entry_point("orchestrator")

# === 并行分支：研究和标题生成同时启动 ===
builder.add_edge("orchestrator", "research")
builder.add_edge("orchestrator", "title_generator")

# === 汇合后顺序执行 ===
builder.add_edge("research", "outline")
builder.add_edge("title_generator", "outline")

builder.add_edge("outline", "writer")
builder.add_edge("writer", "critic")

# === 条件边：Critic 质量关卡 ===
# 达标 → Editor 润色 → 继续后续
# 不达标 → 回到 Writer 重写（反馈注入 Prompt，最多 5 轮）
builder.add_conditional_edges(
    "critic",
    route_after_critic,
    {
        "editor":  "editor",
        "rewrite": "writer",
    }
)
builder.add_edge("editor", "visual")

builder.add_edge("visual", "layout")
builder.add_edge("layout", "final_check")

# === 终审条件边：全自动化 ===
# pass → 发布
# fail → 降级策略：换文章结构模式，回到 Orchestrator 重新规划（最多 2 次）
builder.add_conditional_edges(
    "final_check",
    route_final,
    {
        "publish":   "publisher",
        "regroup":   "orchestrator",   # 降级重做：换结构/换策略
    }
)
builder.add_edge("publisher", END)

# === 编译（带检查点持久化）===
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

---

## 四、状态设计 — 分层解耦

摒弃 God Object，采用**三层状态**：全局元信息 + 各 Agent 独立状态 + 共享工件。

```python
from typing import TypedDict, Literal, Annotated
from operator import add


class ErrorRecord(TypedDict):
    node: str
    error: str
    timestamp: str


class QualityScore(TypedDict):
    dimension: str     # hook / structure / persuasiveness / readability / originality / cta
    score: float       # 0-10
    feedback: str


class WorkflowState(TypedDict):
    # ── 输入 ──
    topic_keyword: str
    dry_run: bool
    config_override: dict  # 可选：覆盖默认配置

    # ── Orchestrator 输出 ──
    topic_category: str        # ai_tools / tech_trends / career / lifestyle
    article_pattern: str       # conflict / listicle / story / essay
    target_audience: str       # 程序员 / 职场人 / 创业者 / 泛科技读者
    writing_strategy: dict     # 写作策略参数

    # ── Research Agent ──
    search_results: list[dict]
    curated_references: list[dict]    # 经过筛选、评分的参考资料
    key_data_points: list[str]        # 提取的关键数据点

    # ── Title Generator ──
    title_candidates: list[dict]      # [{title, rule_score, llm_score, final_score}]
    selected_title: str
    title_score: float

    # ── Outline Agent ──
    outline: dict                     # {hook, sections: [{heading, key_points, data_refs}], cta}

    # ── Writer Agent ──
    draft_article: str
    write_round: int                  # 当前写作轮次
    regroup_round: int                # 降级重做轮次（换结构重跑）

    # ── Critic Agent ──
    quality_scores: list[QualityScore]
    overall_score: float
    critic_feedback: str

    # ── Editor Agent ──
    edited_article: str
    edit_notes: list[str]

    # ── Visual Agent ──
    image_plan: list[dict]            # [{position, prompt, alt_text}]
    article_images: list[dict]        # [{url, wechat_url, alt}]

    # ── Layout Agent ──
    article_html: str

    # ── Publisher Agent ──
    publish_result: dict
    publish_success: bool

    # ── 全局 ──
    errors: Annotated[list[ErrorRecord], add]  # 累积错误（不覆盖，追加）
```

---

## 五、Agent 详细规格

### Agent 1: Orchestrator（路由）

| 项目 | 说明 |
|------|------|
| **职责** | 分析关键词，确定主题分类、目标读者、文章结构模式 |
| **输入** | `topic_keyword` |
| **输出** | `topic_category`, `article_pattern`, `target_audience`, `writing_strategy` |
| **LLM** | 低参数 (temp=0.3)，快速分类 |
| **Prompt 要点** | 给出关键词，从 `[ai_tools, tech_trends, career, lifestyle]` 中选分类；从 `[conflict, listicle, story, essay]` 中选结构 |

**四种文章结构模式：**

| 模式 | 适用场景 | 结构 |
|------|----------|------|
| `conflict` (冲突递进) | 行业趋势、争议话题 | 反常识开头 → 逐层论证 → 行动建议 |
| `listicle` (清单体) | 工具推荐、方法论 | 痛点场景 → N个方法 → 每个配操作 → 总结 |
| `story` (故事驱动) | 人物/案例、个人成长 | 困境 → 转机 → 顿悟 → 启发 |
| `essay` (总分总) | 深度分析、行业解读 | 现象引入 → 核心观点 → 案例 → 升华 |

---

### Agent 2: Research（研究）

| 项目 | 说明 |
|------|------|
| **职责** | 搜索新闻 → 筛选高质量源 → 提取关键数据和引用 |
| **输入** | `topic_keyword`, `writing_strategy` |
| **输出** | `search_results`, `curated_references`, `key_data_points` |
| **LLM** | 用于筛选和提取（temp=0.2），不做生成 |
| **搜索** | SerpAPI，时间过滤限7天内 |

**筛选规则：**
- 来源权威性评分（官媒 > 垂直媒体 > 自媒体）
- 时效性评分（24h 内 > 7 天内）
- 数据密度评分（含具体数字/百分比的优先）
- 与主题相关性评分
- 保留 top 5 篇作为核心参考

---

### Agent 3: Title Generator（标题生成）

| 项目 | 说明 |
|------|------|
| **职责** | 生成 5-8 个候选标题，混合评分选出最佳 |
| **输入** | `topic_keyword`, `topic_category`, `curated_references` |
| **输出** | `title_candidates`, `selected_title`, `title_score` |
| **评分** | 规则评分 (40%) + LLM 评分 (60%) |

**混合评分体系（满分 100）：**

```
最终分 = 规则分 × 0.4 + LLM分 × 0.6

规则分 = 好奇缺口(30) + 价值承诺(25) + 身份认同(20)
       + 数字符号(15) + 长度适配(10)

LLM评分维度:
  - 点击欲望 (1-10): 看到标题是否想点击
  - 信息承诺 (1-10): 标题承诺的信息量
  - 情绪触发 (1-10): 是否引发好奇/惊讶/共鸣
  - 真实匹配 (1-10): 标题与内容的一致性
```

**标题长度规则：** 20-35 字最佳，微信折叠线约 35 字。

---

### Agent 4: Outline（大纲）

| 项目 | 说明 |
|------|------|
| **职责** | 根据 article_pattern 生成结构化大纲，标注数据引用点 |
| **输入** | `curated_references`, `key_data_points`, `article_pattern`, `selected_title` |
| **输出** | `outline` |
| **LLM** | temp=0.4，结构化输出 (JSON) |

**大纲输出格式：**
```json
{
  "hook": {
    "type": "surprising_fact | question | pain_point | story",
    "content": "开头钩子的具体内容描述",
    "data_ref": "引用哪条参考资料的哪个数据"
  },
  "sections": [
    {
      "heading": "小标题",
      "key_points": ["要点1", "要点2"],
      "data_refs": ["引用的参考编号"],
      "word_target": 400
    }
  ],
  "cta": {
    "type": "discussion | share | collection",
    "content": "结尾引导语"
  }
}
```

---

### Agent 5: Writer（写作）

| 项目 | 说明 |
|------|------|
| **职责** | 按大纲逐节写作，注入数据引用和情绪触发点 |
| **输入** | `outline`, `curated_references`, `write_round` |
| **输出** | `draft_article`, `write_round` |
| **LLM** | temp=0.85（创造性），max_tokens=6000 |

**写作 Prompt 核心要求（基于爆款研究）：**
1. 开头 3 句话必须有钩子（反常识/数据/痛点）
2. 每段不超过 100 字
3. 每 300-500 字标注图片插入位 `[IMG:描述]`
4. 数据必须标注来源："据XX数据显示"
5. 正文中段设置一个情绪高潮点
6. 植入 1-2 个社交货币观点（让读者想分享）
7. 结尾包含互动引导 CTA
8. 禁止 AI 味连接词（"首先/其次/最后"、"值得注意的是"）

---

### Agent 6: Critic（评审）

| 项目 | 说明 |
|------|------|
| **职责** | 多维度评分文章质量，给出具体改进建议 |
| **输入** | `draft_article`, `outline`, `curated_references` |
| **输出** | `quality_scores`, `overall_score`, `critic_feedback` |
| **LLM** | temp=0.2（客观评审） |

**六维评分体系（每项 0-10 分）：**

| 维度 | 评分标准 | 权重 |
|------|----------|------|
| **hook 引力** | 开头 3 句是否制造悬念/冲突/痛点 | 20% |
| **结构逻辑** | 段落递进是否清晰，有无跳跃/重复 | 15% |
| **说服力** | 数据引用是否具体，案例是否真实有力 | 20% |
| **可读性** | 段落长度、语言节奏、口语化程度 | 15% |
| **原创性** | 是否有 AI 味/套话，观点是否新颖 | 15% |
| **互动引导** | CTA 是否自然，结尾是否有记忆点 | 15% |

**路由逻辑：**
```python
def route_after_critic(state):
    if state["overall_score"] >= 7.5:
        return "editor"        # 达标，进入润色
    elif state["write_round"] < 5:
        return "rewrite"       # 重写（反馈注入 Writer Prompt）
    else:
        # 5 轮仍不达标，降低温度做最后一次保守修改再走 editor
        return "editor"

def route_final(state):
    if state["overall_score"] >= 7.0:
        return "publish"       # 终审通过，发布
    elif state.get("regroup_round", 0) < 2:
        return "regroup"       # 换结构/换策略，从头重做
    else:
        # 2 次完整重做后仍不达标，以现有结果发布（记录质量警告）
        return "publish"
```

---

### Agent 7: Editor（编辑润色）

| 项目 | 说明 |
|------|------|
| **职责** | 根据 Critic 反馈做针对性修改，不做大幅重写 |
| **输入** | `draft_article`, `quality_scores`, `critic_feedback` |
| **输出** | `edited_article`, `edit_notes` |
| **LLM** | temp=0.5（保守修改） |

**编辑策略：** 只改 Critic 指出的薄弱维度，保持已达标的部分不变。

---

### Agent 8: Visual（视觉）

| 项目 | 说明 |
|------|------|
| **职责** | 规划图片位置 → 生成图片 → 上传微信 |
| **输入** | `edited_article`, `outline` |
| **输出** | `image_plan`, `article_images` |
| **图片** | CogView / DALL-E 3 / placeholder |

**图片规划规则：**
- 每 300-500 字插入一张
- 图片内容与所在段落主题强相关
- 封面图单独生成（16:9 比例）
- 正文图 4:3 比例

---

### Agent 9: Layout（排版）

| 项目 | 说明 |
|------|------|
| **职责** | 将文章 + 图片渲染为微信公众号 HTML |
| **输入** | `edited_article`, `article_images`, `selected_title` |
| **输出** | `article_html` |
| **无 LLM** | 纯模板渲染 |

**微信排版规范：**
```html
<!-- 正文字号 15px，行高 1.75，段间距 15px -->
<p style="margin: 15px 0; font-size: 15px; line-height: 1.75;
          color: #333; letter-spacing: 0.5px;">...</p>
<!-- 小标题 18px 加粗 -->
<h3 style="margin: 30px 0 15px; font-size: 18px;
           font-weight: bold; color: #1a1a1a;">...</h3>
<!-- 图片居中，圆角 -->
<section style="text-align: center; margin: 20px 0;">
  <img src="..." style="width: 100%; border-radius: 6px;">
</section>
```

---

### Agent 10: Publisher（发布）

| 项目 | 说明 |
|------|------|
| **职责** | 创建草稿 / 发布到微信公众号 |
| **输入** | `article_html`, `selected_title`, `article_images[0]` (封面) |
| **输出** | `publish_result`, `publish_success` |
| **无 LLM** | 纯 API 调用 |

**关键改进：**
- 发布前检查 `errors` 列表，严重错误则降级处理（placeholder 图片等），不阻断发布
- 封面图优先使用 Visual Agent 已上传的，避免重复上传
- WeChatClient 单例化，Token 全局共享
- 全自动：无人工审批，质量闭环由 Critic-Writer 循环 + 降级重做保障

---

## 六、提示词工程策略

### 6.1 外部化存储

所有 Prompt 从 `config/prompts/` 目录加载，不在源码中硬编码：

```
config/prompts/
├── orchestrator.md       # 主题分类 Prompt
├── research_filter.md    # 资料筛选 Prompt
├── outline_conflict.md   # 冲突递进大纲 Prompt
├── outline_listicle.md   # 清单体大纲 Prompt
├── outline_story.md      # 故事驱动大纲 Prompt
├── outline_essay.md      # 总分总大纲 Prompt
├── writer.md             # 写作 Prompt（通用部分）
├── critic.md             # 评审 Prompt
├── editor.md             # 编辑润色 Prompt
└── title_scorer.md       # LLM 标题评分 Prompt
```

### 6.2 Prompt 组合

```python
def build_writer_prompt(state):
    """动态组合写作 Prompt"""
    base = load_prompt("writer")                     # 通用写作规则
    pattern = load_prompt(f"writer_{state['article_pattern']}")  # 结构特定指令
    critique = "" if state["write_round"] == 1 else f"""
    ## 上一轮评审反馈（请针对性改进）：
    {state['critic_feedback']}
    ## 薄弱维度：
    {format_low_scores(state['quality_scores'])}
    """
    return base + "\n" + pattern + critique
```

### 6.3 版本化

```
config/prompts/v1/writer.md     # 当前版本
config/prompts/v2/writer.md     # A/B 测试版本
```

通过环境变量 `PROMPT_VERSION=v1` 控制，无需改代码。

---

## 七、错误处理策略

### 7.1 错误分级

| 级别 | 定义 | 处理 |
|------|------|------|
| `FATAL` | 密钥缺失、服务不可用 | 终止流程，记录错误 |
| `RETRYABLE` | 网络超时、API 限流 | 自动重试 3 次（指数退避） |
| `DEGRADABLE` | 图片生成失败、搜索结果不足 | 降级处理（用 placeholder），记录警告 |
| `QUALITY` | 文章评分低于阈值 | Critic-Writer 循环重写 |

### 7.2 错误累积机制

```python
# 每个节点
except RetryableError as e:
    for attempt in range(3):
        try:
            result = retry_operation()
            break
        except:
            wait = 2 ** attempt
    else:
        # 3次都失败
        state["errors"].append(ErrorRecord(
            node="research", error=str(e), timestamp=now()
        ))
        return {"curated_references": [], "key_data_points": []}

# final_check 节点 — 全自动，不阻断
def final_check_node(state):
    fatal_errors = [e for e in state["errors"] if e["severity"] == "FATAL"]
    if fatal_errors:
        # 有致命错误时，用降级内容发布（记录警告），不停下来
        return {"route": "regroup"}  # 换策略重试
    ...
```

---

## 八、配置架构（统一化）

**两层配置取代四层：**

```yaml
# config/settings.yaml — 统一配置文件
workflow:
  max_write_rounds: 5          # Critic-Writer 最大循环轮次
  max_regroup_rounds: 2        # 降级重做最大次数（换结构重跑）
  quality_threshold: 7.5       # Critic 达标分数线
  final_threshold: 7.0         # 终审达标分数线

agents:
  orchestrator:
    model: glm-5
    temperature: 0.3
  research:
    max_results: 8
    recency_days: 7
  title:
    candidate_count: 6
    rule_weight: 0.4
    llm_weight: 0.6
  writer:
    model: glm-5
    temperature: 0.85
    max_tokens: 6000
    word_target: [1500, 2500]
  critic:
    model: glm-5
    temperature: 0.2
  editor:
    model: glm-5
    temperature: 0.5
  visual:
    provider: cogview
    images_per_article: 2

publishing:
  wechat_appid: ${WECHAT_APPID}    # 从环境变量引用
  wechat_secret: ${WECHAT_APPSECRET}
  author: "AI Writer"
```

**环境变量只存密钥：** `.env` 文件仅包含 API Key 等敏感信息，其他所有配置走 `settings.yaml`。

---

## 九、项目目录结构

```
wechat-ai-writer/
├── config/
│   ├── settings.yaml              # 统一配置（取代分散的 JSON/YAML/MD）
│   ├── prompts/                   # 所有 Prompt 模板
│   │   ├── orchestrator.md
│   │   ├── writer.md
│   │   ├── writer_conflict.md
│   │   ├── writer_listicle.md
│   │   ├── critic.md
│   │   ├── editor.md
│   │   └── title_scorer.md
│   └── title_templates.yaml       # 保留，用于规则评分
├── src/
│   ├── main.py                    # CLI + FastAPI
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py               # WorkflowState 定义
│   │   ├── workflow.py            # StateGraph 构建 + 条件边
│   │   └── routers.py             # 路由函数 (route_after_critic 等)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # 主题分类 + 策略选择
│   │   ├── research.py            # 搜索 + 筛选 + 提取
│   │   ├── title_generator.py     # 多标题生成 + 混合评分
│   │   ├── outline.py             # 大纲生成
│   │   ├── writer.py              # 分节写作
│   │   ├── critic.py              # 六维评分
│   │   ├── editor.py              # 针对性修改
│   │   ├── visual.py              # 图片规划 + 生成
│   │   ├── layout.py              # HTML 排版
│   │   └── publisher.py           # 微信发布
│   ├── llm/
│   │   ├── __init__.py            # create_llm() 工厂
│   │   └── base.py                # 统一 OpenAI 兼容客户端（合并3个类）
│   ├── search/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── serpapi.py
│   ├── wechat/
│   │   ├── __init__.py
│   │   └── client.py              # 单例化，Token 缓存
│   ├── image/
│   │   └── generator.py
│   └── utils/
│       ├── config.py              # YAML 配置加载 + 环境变量
│       ├── logger.py
│       └── retry.py               # 重试装饰器
├── tests/
│   ├── test_agents/
│   │   ├── test_critic.py
│   │   ├── test_writer.py
│   │   └── test_title_generator.py
│   ├── test_graph/
│   │   └── test_workflow.py
│   └── conftest.py                # Mock fixtures
├── outputs/
├── logs/
├── .env                           # 仅密钥
├── .env.example
├── requirements.txt
└── ARCHITECTURE.md                # 本文档
```

---

## 十、迁移路径（渐进式）

### Phase 1：基础重构（1 周）

**目标：** 修复安全和可靠性问题，不改变流程。

1. 轮换所有密钥，`.env` 加入 `.gitignore`
2. GlobalState 增加 `errors` 字段
3. 所有 Prompt 从 `config/prompts/` 外部加载（替换 `generate.py` 中的内联 Prompt）
4. 合并三个 LLM 类为 `OpenAICompatibleLLM`
5. 删除死代码（未使用的 Pydantic 模型、TitleOptimizer 独立模块）
6. WeChatClient 单例化

### Phase 2：引入 Critic-Editor 循环（1 周）

**目标：** 质量控制闭环，全自动优化。

1. 实现 Critic Agent（六维评分）
2. 实现 Editor Agent（针对性修改）
3. 添加条件边：critic → editor 或 critic → rewrite（最多 5 轮）
4. 实现 `write_round` 计数，每轮逐步降低 Writer temperature
5. 实现 `final_check` 质量关卡 + 降级重做（`regroup_round`，换结构回 Orchestrator）
6. 全程无人工介入，质量闭环由多轮循环保障

### Phase 3：多 Agent 完善（1 周）

**目标：** 完整多 Agent 系统。

1. 实现 Orchestrator（主题分类 + 策略选择）
2. 实现 Title Generator（混合评分）
3. 实现 Outline Agent（四种结构模式）
4. 实现 Visual Agent（智能图片规划）
5. 并行分支：research 和 title_generator 同时启动
6. 统一配置到 `settings.yaml`

### Phase 4：生产强化（持续）

1. 实现 MemorySaver 检查点持久化（失败可恢复）
2. FastAPI 端点添加认证 + `asyncio.to_thread()` 包装
3. 核心路径集成测试
4. Prompt A/B 测试框架
5. 质量趋势监控：记录每篇文章各轮评分，分析优化效果

---

## 十一、关键设计决策及理由

| 决策 | 理由 |
|------|------|
| Critic 用 LLM 评分而非纯规则 | 规则无法评估"情绪共鸣""原创性"等软性维度 |
| 最多 5 轮 Writer-Critic 循环 | 自动化闭环，5 轮覆盖大部分质量提升空间 |
| 终审不达标则降级重做（换结构） | 某种结构可能天然不适合该主题，换一种重试比死磕更有效 |
| 降级重做最多 2 次 | 防止无限循环，2 次后以现有最好结果发布 |
| 无人工介入 | 全自动运行，适合定时发布场景，降低运营成本 |
| 标题混合评分（规则+LLM） | 规则保障基础质量（长度/数字），LLM 评估语义吸引力 |
| 4 种文章结构而非自由生成 | 约束 = 可控，自由生成导致结构混乱、AI 味重 |
| Prompt 全部外部化 | 不改代码即可迭代 Prompt，支持 A/B 测试 |
| `errors` 用 `Annotated[list, add]` 追加 | LangGraph 默认覆盖，`add` 操作符确保错误不丢失 |
| 配置统一到 YAML | 当前 4 层配置（env + JSON + YAML + MD）中 3 层是死代码 |

---

## 十二、预期效果

| 指标 | 当前系统 | 升级后 |
|------|----------|--------|
| 文章质量评分 | 无评分（有就发） | ≥ 7.5/10 才过 Critic，≥ 7.0/10 才发布 |
| 质量不达标处理 | 无（直接发布） | 自动循环优化，最多 5 轮 Critic-Writer + 2 次降级重做 |
| 标题质量 | 使用 topic 原文 | 6 候选混合评分选出最优 |
| 错误处理 | 吞掉异常，发垃圾 | 错误累积记录，降级重做而非阻断 |
| 写作模式 | 单一固定结构 | 4 种模式按主题自动选择 |
| 人工介入 | 无 | 无（全自动） |
| 可维护性 | Prompt 在源码里 | Prompt 外部化，改配置不改代码 |
| 可测试性 | 不可测试 | 各 Agent 可独立单元测试 |
| 容错能力 | 不可恢复 | Checkpoint 持久化，可断点续跑 |
