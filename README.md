# WeChat AI Writer - 微信公众号AI写作助手

> 🚀 **完全独立** - 无Coze依赖，100%本地运行
> 
> 基于 LangGraph 的智能公众号内容生成系统

## ✨ 核心特性

- 🔄 **7步工作流**: 搜索 → 提取 → 深挖 → 写作 → 配图 → 排版 → 发布
- 🤖 **多LLM支持**: 
  - ✅ **GLM-5** (智谱AI，推荐) - 中文优化，价格实惠（¥0.005/千tokens）
  - ✅ OpenAI - 国际标准
  - ✅ 豆包 - 字节跳动
- 🌐 **多搜索源**: SerpAPI / Google / Bing
- 📱 **微信集成**: 自动上传图片、创建草稿、一键发布
- 🎨 **智能配图**: 自动生成相关配图
- 📊 **完整日志**: loguru日志系统
- ⚡ **快速部署**: 5分钟启动

## 🏗️ 架构设计

```
输入: topic_keyword (关键词)
  ↓
[1] search_tech_news      # 网络搜索科技新闻
  ↓
[2] extract_topic         # LLM主题抽取 (GLM-5/0.3温度)
  ↓
[3] deep_search           # 深度搜索相关内容
  ↓
[4] generate_article      # LLM文章生成 (GLM-5/0.9温度)
  ↓
[5] generate_images       # 生成配图
  ↓
[6] add_images            # 插入图片到文章
  ↓
[7] publish_to_wechat     # 发布到公众号
  ↓
输出: publish_result (发布结果)
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd ~/clawd/projects/wechat-ai-writer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，选择一个 LLM 提供商并填入 API key

# 推荐使用智谱 GLM-5（中文优化，价格实惠）
# .env 中设置:
# LLM_PROVIDER=glm
# ZAI_API_KEY=your_zhipu_key
```

**获取 GLM-5 API Key**:
1. 访问 https://open.bigmodel.cn/
2. 注册账号（支持手机号）
3. 创建 API Key
4. 新用户有免费额度

### 3. 运行工作流

```bash
# 完整流程（测试模式）
python src/main.py --keyword "人工智能" --dry-run

# 本地测试（不发布）
python src/main.py --keyword "人工智能" --dry-run

# 正式运行（发布到微信）
python src/main.py --keyword "人工智能"

# 启动 HTTP 服务
python src/main.py --server --port 5000
```

## 📁 项目结构

```
wechat-ai-writer/
├── src/
│   ├── core/              # 核心工作流
│   │   ├── workflow.py    # LangGraph 主流程
│   │   ├── state.py       # 状态定义
│   │   └── nodes/         # 7个节点实现
│   │       ├── search.py
│   │       ├── extract.py
│   │       ├── deep_search.py
│   │       ├── generate.py
│   │       ├── images.py
│   │       ├── layout.py
│   │       └── publish.py
│   ├── llm/               # LLM 集成
│   │   ├── base.py        # 基础类
│   │   ├── openai.py      # OpenAI
│   │   ├── doubao.py      # 豆包
│   │   └── glm5.py        # GLM-5（新增）
│   ├── search/            # 搜索集成
│   │   ├── base.py        # 基础类
│   │   └── serpapi.py     # SerpAPI
│   ├── wechat/            # 微信集成
│   │   └── client.py      # 微信客户端
│   ├── image/             # 图片生成
│   │   └── generator.py
│   └── utils/             # 工具类
│       ├── logger.py      # 日志系统
│       └── config.py      # 配置管理
├── config/                # 配置文件
│   ├── llm/               # LLM 配置
│   │   ├── extract.json   # 主题抽取配置
│   │   └── generate.json  # 文章生成配置
│   └── prompts/           # 提示词模板
│       ├── extract.txt
│       └── generate.txt
├── tests/                 # 测试
├── docs/                  # 文档
│   ├── ARCHITECTURE.md    # 架构设计
│   ├── DEPLOYMENT.md      # 部署指南
│   ├── API.md             # API文档
│   └── GLM5_INTEGRATION.md # GLM-5集成指南（新增）
├── scripts/               # 脚本
│   ├── setup.sh           # 环境配置
│   └── test.sh            # 测试脚本
├── .env.example           # 环境变量模板
├── requirements.txt       # Python依赖
└── README.md              # 本文件
```

## 🔧 配置说明

### 环境变量

```bash
# LLM 配置（推荐 GLM-5）
LLM_PROVIDER=glm              # glm, openai, 或 doubao
ZAI_API_KEY=your_key          # 智谱 GLM-5 API Key（推荐）
OPENAI_API_KEY=sk-xxx         # OpenAI API Key（可选）
DOUBAO_API_KEY=your_key       # 豆包 API Key（可选）

# 搜索配置
SEARCH_PROVIDER=serpapi       # serpapi, google, bing
SERPAPI_KEY=your_key          # SerpAPI Key

# 微信配置（可选）
WECHAT_ACCESS_TOKEN=your_token   # 微信 Access Token

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### LLM 配置

**主题抽取** (`config/llm/extract.json`):
```json
{
  "model": "glm-5",
  "temperature": 0.3,
  "max_tokens": 2000,
  "top_p": 0.9
}
```

**文章生成** (`config/llm/generate.json`):
```json
{
  "model": "glm-5",
  "temperature": 0.9,
  "max_tokens": 8000,
  "top_p": 0.98
}
```

## 📊 核心功能

### 1. 智能主题抽取

- **聚焦单一故事点**，避免大而全
- **提取具体场景**，有人物、事件、细节
- **温度0.3**，确保准确性

### 2. 自然文章生成

- **故事驱动**，细节为王
- **生活化语言**，无AI味
- **温度0.9**，创造性强

### 3. 多LLM支持

#### GLM-5（推荐）
- 中文优化
- 价格实惠（¥0.005/千tokens）
- 新用户免费额度
- 国内服务器，响应快

#### OpenAI
- 国际标准
- GPT-4 模型
- 按量计费

#### 豆包
- 字节跳动
- 中文优化
- 价格适中

### 4. 微信公众号集成

- 自动上传图片
- 创建图文草稿
- 一键发布文章
- 查询发布状态

## 🎯 使用场景

1. **科技媒体**: 每日科技资讯自动生成
2. **企业公众号**: 行业动态自动化报道
3. **个人博客**: 技术文章快速生成
4. **内容创作**: AI辅助写作流程

## 💰 成本估算

| 服务 | 费用 | 备注 |
|------|------|------|
| SerpAPI | $50/月 | 5000次搜索 |
| **GLM-5** | **¥0.005/千tokens** | **中文优化，推荐** |
| 豆包 API | ¥0.008/千tokens | 主题抽取 |
| OpenAI | $0.03/千tokens | 国际标准 |
| 微信 API | 免费 | 公众号API |

**推荐方案** (GLM-5): ~¥5/月 (100篇文章)  
**成本对比**: GLM-5 比 OpenAI 便宜 6倍

## 🔒 安全建议

1. **Access Token 管理**
   - 定期更新（2小时有效期）
   - 使用环境变量存储
   - 不要提交到代码仓库

2. **API Key 保护**
   - 使用 .env 文件
   - 加入 .gitignore
   - 生产环境使用密钥管理服务

## 📝 开发计划

- [x] 核心工作流实现
- [x] LLM 集成（豆包/OpenAI）
- [x] SerpAPI 搜索集成
- [x] 微信公众号集成
- [x] **GLM-5 集成**（新增）
- [ ] 图片生成（DALL-E/Stable Diffusion）
- [ ] 多语言支持
- [ ] Web UI 界面
- [ ] 定时任务调度

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**开发者**: Nano (OpenClaw AI)  
**创建时间**: 2026-03-25  
**GLM-5集成**: 2026-03-26  
**版本**: 1.1.0
