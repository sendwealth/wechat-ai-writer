# 图片生成集成指南

## 🎨 概述

WeChat AI Writer 支持三种图片生成方案：

| 方案 | 价格 | 质量 | 速度 | 推荐度 |
|------|------|------|------|--------|
| **CogView** | **¥0.06/张** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **DALL-E 3** | **$0.04/张** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Placeholder** | **免费** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 💰 成本对比

### 单篇文章（2张配图）

| 方案 | 成本 | 对比 |
|------|------|------|
| **CogView** | **¥0.12** | 基准 |
| **DALL-E 3** | **¥0.58** | **贵 383%** |
| **Placeholder** | **¥0** | 免费（测试用） |

### 月度成本（100篇文章 = 200张图）

| 方案 | 成本 | 年成本 |
|------|------|--------|
| **CogView** | **¥12** | ¥144 |
| **DALL-E 3** | **¥58** | ¥696 |
| **节省** | **¥46/月** | **¥552/年** |

---

## 🚀 快速开始

### 方案1: CogView（推荐）⭐⭐⭐⭐⭐

**优势**:
- ✅ 与 GLM-5 共用 API Key（无需额外配置）
- ✅ 价格便宜（¥0.06/张）
- ✅ 中文优化（理解中文提示词）
- ✅ 质量优秀（4星）

**配置**:
```bash
# .env 文件
IMAGE_PROVIDER=cogview
ZAI_API_KEY=your_glm5_key  # 与 GLM-5 共用
```

**价格**:
- 标准请求: ¥0.06/张
- 批量请求: ¥0.03/张

**获取 API Key**:
1. 访问 https://open.bigmodel.cn/
2. 注册并获取 API Key
3. 与 GLM-5 共用同一个 Key

---

### 方案2: DALL-E 3 ⭐⭐⭐⭐

**优势**:
- ✅ 质量最高（5星）
- ✅ 支持多种尺寸
- ✅ 支持高清模式

**劣势**:
- ⚠️ 价格贵（$0.04/张 ≈ ¥0.29）
- ⚠️ 需要 OpenAI API Key
- ⚠️ 需要国际信用卡

**配置**:
```bash
# .env 文件
IMAGE_PROVIDER=dalle3
OPENAI_API_KEY=sk-xxx
```

**价格**:
- 标准 1024x1024: $0.04/张
- HD 1024x1024: $0.08/张
- HD 1024x1792: $0.12/张

**获取 API Key**:
1. 访问 https://platform.openai.com/
2. 注册并获取 API Key
3. 需要国际信用卡充值

---

### 方案3: Placeholder（测试用）⭐⭐⭐

**用途**: 本地开发测试

**配置**:
```bash
# .env 文件
IMAGE_PROVIDER=placeholder
```

**特点**:
- ✅ 免费
- ✅ 快速
- ⚠️ 不是真实图片

---

## 🔧 完整配置示例

### 使用 CogView（推荐）

```bash
# .env 文件

# LLM 配置
LLM_PROVIDER=glm
ZAI_API_KEY=your_glm5_key

# 搜索配置
SERPAPI_KEY=your_serpapi_key

# 图片生成配置（与 GLM-5 共用 Key）
IMAGE_PROVIDER=cogview

# 微信配置
WECHAT_APPID=wxXXXXXXXX
WECHAT_APPSECRET=your_secret
```

### 使用 DALL-E 3

```bash
# .env 文件

# LLM 配置
LLM_PROVIDER=glm
ZAI_API_KEY=your_glm5_key

# 搜索配置
SERPAPI_KEY=your_serpapi_key

# 图片生成配置
IMAGE_PROVIDER=dalle3
OPENAI_API_KEY=sk-xxx

# 微信配置
WECHAT_APPID=wxXXXXXXXX
WECHAT_APPSECRET=your_secret
```

---

## 📝 使用方法

### 自动生成（推荐）

```bash
# 生成文章时自动生成配图
python src/main.py --keyword "人工智能" --dry-run
```

工作流会自动：
1. 提取文章主题和亮点
2. 为每个亮点生成配图
3. 插入到文章中

### 手动测试

```python
from image import generate_article_images

# 生成图片
images = generate_article_images(
    topic="人工智能",
    highlights=["深度学习", "神经网络"],
    num_images=2,
    provider="cogview"
)

# 查看结果
for img in images:
    print(f"URL: {img['url']}")
    print(f"Alt: {img['alt']}")
```

---

## 🎯 最佳实践

### 1. 提示词优化

**好的提示词**:
```
为科技文章'人工智能的未来'生成配图，要求现代、科技感、高质量
```

**差的提示词**:
```
AI
```

### 2. 成本控制

**建议**:
- 使用 CogView（便宜 83%）
- 批量生成（¥0.03/张）
- 缓存图片（避免重复生成）

### 3. 质量优化

**CogView 设置**:
```python
images = generate_article_images(
    topic="主题",
    highlights=["亮点1", "亮点2"],
    num_images=2,
    provider="cogview"
)
```

**DALL-E 3 设置**:
```python
from image import DALLE3Generator

generator = DALLE3Generator()
result = generator.generate(
    prompt="描述",
    quality="hd",  # 高清模式
    size="1024x1792"  # 竖版
)
```

---

## 🐛 常见问题

### Q1: 图片生成失败？

**原因**: API Key 未配置或无效

**解决**:
```bash
# 检查配置
cat .env | grep IMAGE_PROVIDER
cat .env | grep ZAI_API_KEY  # CogView
cat .env | grep OPENAI_API_KEY  # DALL-E 3
```

### Q2: 成本太高？

**解决**:
1. 使用 CogView（便宜 83%）
2. 使用批量 API（再便宜 50%）
3. 减少配图数量（1张/篇）

### Q3: 质量不满意？

**解决**:
1. 优化提示词（更详细）
2. 使用 DALL-E 3 HD 模式
3. 多生成几张，选择最好的

---

## 📊 性能对比

| 指标 | CogView | DALL-E 3 |
|------|---------|----------|
| **生成速度** | 5-10秒 | 10-20秒 |
| **成功率** | 95% | 98% |
| **中文理解** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **图片质量** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **价格** | ⭐⭐⭐⭐⭐ | ⭐⭐ |

---

## 🎉 总结

**推荐配置**:
```bash
IMAGE_PROVIDER=cogview
ZAI_API_KEY=your_key
```

**理由**:
- ✅ 与 GLM-5 共用 Key（配置简单）
- ✅ 价格便宜（¥0.06/张）
- ✅ 中文优化（理解提示词）
- ✅ 质量优秀（4星）

**成本优化**:
- 使用 CogView：¥12/月（100篇文章）
- 比 DALL-E 3 节省：¥46/月（¥552/年）

---

**文档创建**: 2026-03-26 23:05
**适用版本**: WeChat AI Writer v1.2.0+
**状态**: ✅ 生产就绪
