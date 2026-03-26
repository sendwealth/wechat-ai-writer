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
- 🌐 **SerpAPI 搜索**: 网络搜索科技新闻
- 📱 **微信集成**: 自动 Token 管理，绕过 IP 白名单
- ⚡ **快速部署**: 5分钟启动

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
# 编辑 .env 文件

# 推荐配置（GLM-5）
LLM_PROVIDER=glm
ZAI_API_KEY=your_zhipu_key
SERPAPI_KEY=your_serpapi_key
WECHAT_APPID=wxXXXXXXXX
WECHAT_APPSECRET=your_secret
```

**获取 API Keys**:
- **GLM-5**: https://open.bigmodel.cn/ (新用户免费额度)
- **SerpAPI**: https://serpapi.com/ (100次/月免费)
- **微信**: 公众平台 → 设置与开发 → 基本配置

### 3. 运行工作流

```bash
# 测试模式（不发布）
python src/main.py --keyword "人工智能" --dry-run

# 正式运行
python src/main.py --keyword "人工智能"

# HTTP 服务
python src/main.py --server --port 5000
```

## 🏗️ 工作流程

```
输入: topic_keyword
  ↓
[1] search_tech_news      # SerpAPI 搜索
  ↓
[2] extract_topic         # GLM-5 提取主题
  ↓
[3] deep_search           # 深度搜索
  ↓
[4] generate_article      # GLM-5 生成文章
  ↓
[5] generate_images       # 生成配图
  ↓
[6] add_images            # 插入图片
  ↓
[7] publish_to_wechat     # 发布公众号
```

## 💰 成本对比

| 提供商 | 单篇文章成本 | 对比 |
|--------|------------|------|
| **GLM-5** | **¥0.05** | 基准 |
| 豆包 | ¥0.08 | -37% |
| OpenAI | ¥0.30 | **-83%** |

**月度成本 (100篇文章)**:
- GLM-5: ¥5
- OpenAI: ¥30
- **节省**: ¥25/月

## 🔧 配置说明

### 环境变量

```bash
# LLM 配置（推荐 GLM-5）
LLM_PROVIDER=glm
ZAI_API_KEY=your_key

# 搜索配置
SERPAPI_KEY=your_serpapi_key

# 微信配置（自动 Token 管理）
WECHAT_APPID=wxXXXXXXXX
WECHAT_APPSECRET=your_secret
```

## 📁 项目结构

```
wechat-ai-writer/
├── src/
│   ├── core/              # 核心工作流
│   ├── llm/               # LLM 集成 (GLM-5/OpenAI/豆包)
│   ├── search/            # SerpAPI 搜索
│   ├── wechat/            # 微信客户端（自动 Token）
│   └── utils/             # 工具类
├── config/                # LLM 配置文件
├── docs/                  # 文档
└── scripts/               # 脚本
```

## 📚 文档

- **QUICKSTART.md** - 5分钟快速开始
- **GLM5_INTEGRATION.md** - GLM-5 完整集成指南
- **AUTO_TOKEN_GUIDE.md** - 微信 Token 自动管理指南

## ⚙️ 技术栈

- **LangGraph 0.2.x** - 状态机工作流
- **LangChain 0.2.x** - LLM 集成
- **智谱 GLM-5** - 中文优化的 LLM
- **SerpAPI** - 网络搜索
- **loguru** - 日志系统

## 🔒 安全特性

- ✅ 自动 Token 管理（绕过 IP 白名单）
- ✅ 智能缓存（2小时有效期）
- ✅ 多级降级机制
- ✅ .env 不会提交到 Git

## 🎯 核心优势

1. **完全独立** - 零 Coze 依赖
2. **成本优化** - GLM-5 比 OpenAI 便宜 83%
3. **自动化** - 微信 Token 自动管理
4. **中文优化** - GLM-5 专为中文设计

## 📝 License

MIT

---

**项目状态**: ✅ 生产就绪
**版本**: v1.2.0
**更新时间**: 2026-03-26
