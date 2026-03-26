# WeChat AI Writer - 快速开始指南

## 🎯 5分钟快速启动

### 1. 环境准备

```bash
cd ~/clawd/projects/wechat-ai-writer
bash scripts/setup.sh
```

### 2. 配置 API Keys

编辑 `.env` 文件：

```bash
# 必填：LLM 配置（二选一）
LLM_PROVIDER=doubao
DOUBAO_API_KEY=your_doubao_key

# 必填：搜索配置
SERPAPI_KEY=your_serpapi_key

# 可选：微信配置（不配置则无法发布）
WECHAT_ACCESS_TOKEN=your_wechat_token
```

### 3. 测试运行

```bash
# 激活虚拟环境
source venv/bin/activate

# 测试模式（不发布）
python src/main.py --keyword "人工智能" --dry-run
```

### 4. 正式运行

```bash
# 完整流程（发布到微信）
python src/main.py --keyword "量子计算"
```

### 5. HTTP 服务

```bash
# 启动 API 服务
python src/main.py --server --port 5000

# 调用 API
curl -X POST http://localhost:5000/run \
  -H "Content-Type: application/json" \
  -d '{"keyword": "区块链", "dry_run": true}'
```

## 📊 工作流程

```
输入关键词
  ↓
搜索科技新闻 (SerpAPI)
  ↓
LLM 提取主题 (豆包/0.3温度)
  ↓
深度搜索 (SerpAPI)
  ↓
LLM 生成文章 (豆包/0.9温度)
  ↓
生成配图 (占位符)
  ↓
插入图片
  ↓
发布到微信 (可选)
```

## 🔧 常见问题

### Q1: SerpAPI 如何获取？

1. 访问 https://serpapi.com/
2. 注册账号
3. 获取 API Key
4. 免费额度：100次/月

### Q2: 豆包 API 如何获取？

1. 访问 https://www.volcengine.com/
2. 开通豆包大模型
3. 获取 API Key
4. 充值（按量计费）

### Q3: 微信 Access Token 如何获取？

参考原项目的 `docs/WECHAT_CONFIG.md`

### Q4: 如何切换到 OpenAI？

编辑 `.env`:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
```

## 💡 高级用法

### 自定义 LLM 配置

编辑 `config/llm/extract.json` 和 `config/llm/generate.json`

### 查看日志

```bash
tail -f logs/app.log
```

### 保存输出

所有结果自动保存到 `outputs/` 目录

## 📈 性能优化

- **并行搜索**: 修改 `search` 节点支持并行
- **缓存结果**: 缓存搜索和 LLM 结果
- **流式输出**: 支持 SSE 流式响应

## 🔒 安全建议

1. **不要提交 .env 文件**
2. **定期更新 Access Token**
3. **限制 API 调用频率**

---

**需要帮助？** 查看 `docs/` 目录下的详细文档
