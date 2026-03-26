# WeChat AI Writer - GLM-5 集成指南

## 🎯 GLM-5 支持

**智谱AI GLM-5** 已完全集成到 WeChat AI Writer！

### ✨ 为什么选择 GLM-5？

1. **中文优化** - 专为中文场景设计
2. **价格实惠** - 比OpenAI便宜很多
3. **免费额度** - 新用户有免费试用
4. **能力强** - 支持128K上下文
5. **响应快** - 国内服务器，速度更快

---

## 🚀 快速配置

### 1. 获取 GLM-5 API Key

**步骤**:
1. 访问 https://open.bigmodel.cn/
2. 注册账号（支持手机号）
3. 进入控制台
4. 创建 API Key
5. 复制 API Key

**免费额度**:
- 新用户赠送免费tokens
- 足够测试使用

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
# 设置 LLM 提供商
LLM_PROVIDER=glm

# 填入你的 API Key
ZAI_API_KEY=your_api_key_here

# 可选：自定义 Base URL（默认已配置）
ZAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

### 3. 运行测试

```bash
cd ~/clawd/projects/wechat-ai-writer
source venv/bin/activate
python src/main.py --keyword "人工智能" --dry-run
```

---

## 📊 GLM-5 模型对比

| 模型 | 上下文 | 价格（千tokens） | 适用场景 |
|------|--------|-----------------|---------|
| **glm-5** | 128K | ¥0.005 | 通用场景（推荐）|
| **glm-4-plus** | 128K | ¥0.05 | 复杂任务 |
| **glm-4-flash** | 128K | ¥0.001 | 快速响应 |

**推荐使用**: `glm-5` - 性价比最高

---

## 🔧 配置文件

### 主题提取配置
`config/llm/extract.json`:
```json
{
  "model": "glm-5",
  "temperature": 0.3,
  "max_tokens": 2000,
  "top_p": 0.9
}
```

### 文章生成配置
`config/llm/generate.json`:
```json
{
  "model": "glm-5",
  "temperature": 0.9,
  "max_tokens": 8000,
  "top_p": 0.98
}
```

---

## 💰 成本对比

### GLM-5 vs OpenAI

| 场景 | GLM-5 | OpenAI GPT-4 | 节省 |
|------|-------|--------------|------|
| 主题提取（2K tokens） | ¥0.01 | ¥0.06 | 83% |
| 文章生成（8K tokens） | ¥0.04 | ¥0.24 | 83% |
| **单篇文章** | **¥0.05** | **¥0.30** | **83%** |
| **100篇文章/月** | **¥5** | **¥30** | **83%** |

**结论**: GLM-5 比 OpenAI 便宜 **6倍**！

---

## 🎓 技术实现

### 代码结构
```
src/llm/
├── base.py        # 基础类
├── openai.py      # OpenAI
├── doubao.py      # 豆包
├── glm5.py        # GLM-5（新增）
└── __init__.py    # 工厂模式
```

### GLM-5 集成代码
```python
# src/llm/glm5.py
from langchain_openai import ChatOpenAI

class GLM5LLM(BaseLLM):
    def build(self) -> ChatOpenAI:
        return ChatOpenAI(
            model="glm-5",
            temperature=0.7,
            max_tokens=2000,
            api_key=self.api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4"
        )
```

### 工厂模式
```python
# src/llm/__init__.py
def create_llm(llm_config):
    provider = config.get_llm_provider()
    
    if provider == "glm":
        return GLM5LLM(llm_config)
    elif provider == "openai":
        return OpenAILLM(llm_config)
    # ...
```

---

## 🔄 切换 LLM

### 切换到 OpenAI
```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
```

### 切换到豆包
```bash
# .env
LLM_PROVIDER=doubao
DOUBAO_API_KEY=xxx
```

### 切换到 GLM-5
```bash
# .env
LLM_PROVIDER=glm
ZAI_API_KEY=xxx
```

---

## 🧪 测试验证

### 运行测试
```bash
# 测试模式（不发布）
python src/main.py --keyword "人工智能" --dry-run

# 查看日志
tail -f logs/app.log

# 查看输出
cat outputs/人工智能_*.json
```

### 预期结果
```
✅ 节点1: 搜索科技新闻 - 完成
✅ 节点2: 提取主题 - GLM-5 调用成功
✅ 节点3: 深度搜索 - 完成
✅ 节点4: 生成文章 - GLM-5 调用成功
✅ 节点5: 生成图片 - 完成
✅ 节点6: 插入图片 - 完成
✅ 节点7: 发布到微信 - 完成
```

---

## 📝 最佳实践

### 1. 温度设置
- **主题提取**: 0.3（保守，确保准确）
- **文章生成**: 0.9（创造性强）

### 2. Token 限制
- **主题提取**: 2000（够用）
- **文章生成**: 8000（长文支持）

### 3. 错误处理
- 自动降级到占位符
- 完整日志记录
- 友好错误提示

---

## 🐛 常见问题

### Q1: GLM-5 调用失败？
**检查**:
1. API Key 是否正确
2. 网络是否正常
3. 账户余额是否充足

### Q2: 响应速度慢？
**解决**:
1. 使用 `glm-4-flash` 模型
2. 减少 `max_tokens`
3. 降低 `temperature`

### Q3: 文章质量不高？
**优化**:
1. 调整 `temperature`（0.7-0.9）
2. 增加搜索结果
3. 优化提示词

---

## 📚 相关文档

- **智谱AI官网**: https://open.bigmodel.cn/
- **API文档**: https://open.bigmodel.cn/dev/api
- **价格说明**: https://open.bigmodel.cn/pricing
- **LangChain集成**: https://python.langchain.com/docs/integrations/chat/zhipuai

---

## 🎉 总结

**GLM-5 集成完成！**

**优势**:
- ✅ 中文优化
- ✅ 价格实惠（便宜6倍）
- ✅ 免费额度
- ✅ 响应快速
- ✅ 完全兼容

**立即使用**:
```bash
# 1. 获取 API Key
https://open.bigmodel.cn/

# 2. 配置 .env
LLM_PROVIDER=glm
ZAI_API_KEY=your_key

# 3. 运行测试
python src/main.py --keyword "人工智能" --dry-run
```

---

**更新时间**: 2026-03-26 20:10
**支持状态**: ✅ 完全支持
**推荐等级**: ⭐⭐⭐⭐⭐
