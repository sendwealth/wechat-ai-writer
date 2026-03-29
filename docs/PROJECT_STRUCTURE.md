# WeChat AI Writer 项目结构

## 📁 目录结构

```
wechat-ai-writer/
├── config/                  # 配置文件
│   ├── llm/                # LLM 配置
│   ├── prompts/            # 提示词模板
│   └── title_templates.yaml # 标题模板
├── docs/                   # 文档
│   ├── QUICKSTART.md      # 快速开始
│   ├── AUTO_TOKEN_GUIDE.md # Token 自动管理
│   ├── GLM5_INTEGRATION.md # GLM-5 集成
│   ├── IMAGE_GENERATION_GUIDE.md # 图片生成
│   └── OPTIMIZATION_PLAN.md # 优化计划（合并版）
├── src/                    # 源代码
│   ├── core/              # 核心逻辑
│   ├── llm/               # LLM 集成
│   ├── search/            # 搜索模块
│   ├── image/             # 图片生成
│   └── wechat/            # 微信集成
├── outputs/                # 生成结果
├── logs/                   # 日志文件
├── README.md              # 项目说明
└── requirements.txt       # 依赖列表
```

## 📚 文档说明

### 用户文档
- **README.md** - 项目总览和快速开始
- **docs/QUICKSTART.md** - 5分钟快速开始指南
- **docs/AUTO_TOKEN_GUIDE.md** - 微信 Token 自动管理
- **docs/GLM5_INTEGRATION.md** - GLM-5 集成指南
- **docs/IMAGE_GENERATION_GUIDE.md** - 图片生成指南

### 开发文档
- **docs/OPTIMIZATION_PLAN.md** - 完整优化计划（Phase 1-3）
- **config/** - 配置文件和模板

## 🗑️ 已删除的冗余文件

以下文件已合并或删除：
- ~~docs/OPTIMIZATION_PLAN_OVERVIEW.md~~ → 合并到 OPTIMIZATION_PLAN.md
- ~~docs/OPTIMIZATION_PLAN_PHASE1.md~~ → 合并到 OPTIMIZATION_PLAN.md
- ~~docs/OPTIMIZATION_PLAN_PHASE2.md~~ → 合并到 OPTIMIZATION_PLAN.md
- ~~docs/OPTIMIZATION_PLAN_PHASE3.md~~ → 合并到 OPTIMIZATION_PLAN.md
- ~~docs/OPTIMIZATION_COMPLETION_REPORT.md~~ → 合并到 OPTIMIZATION_PLAN.md
- ~~test_optimization.py~~ → 删除（测试已完成）

---

_最后更新: 2026-03-29_
