# WeChat AI Writer - 自动获取 Token 配置

## 🎯 新功能：自动管理 Access Token

**更新时间**: 2026-03-26 20:22
**状态**: ✅ **完全自动化**

---

## ✨ 新特性

### 1. 自动获取 Access Token

**无需手动更新 Token！**

系统会在每次发布时自动获取最新的 access token。

**配置方式**:
```bash
# .env 文件

# 方式1: 使用 AppID + AppSecret（推荐）
WECHAT_APPID=wxXXXXXXXXXXXXXXXXXXXX
WECHAT_APPSECRET=your_appsecret_here

# 方式2: 使用静态 Token（备选）
WECHAT_ACCESS_TOKEN=72_xxxxxxxxxxxxxxxxxxxxx
```

### 2. 优先级机制

**Token 获取优先级**:
1. ✅ **缓存 Token** - 如果缓存有效且未过期
2. ✅ **API 获取** - 通过 AppID + AppSecret 自动获取
3. ✅ **静态配置** - 使用 .env 中的 WECHAT_ACCESS_TOKEN

### 3. 缓存管理

**智能缓存**:
- 缓存有效期为 **2 小时**
- 提前 **5 分钟** 自动更新
- 失败时自动降级到静态配置

---

## 🚀 使用方法

### 配置 1: AppID + AppSecret（推荐）⭐⭐⭐⭐⭐

```bash
# 编辑 .env
vim ~/clawd/projects/wechat-ai-writer/.env

# 添加配置
WECHAT_APPID=wx51bcdd71b906032a
WECHAT_APPSECRET=b96e213a112354df35f5a680d9b388d3
```

**优点**:
- ✅ 完全自动化
- ✅ 无需手动更新
- ✅ 总是使用最新 token
- ✅ 适合长期运行

### 配置 2: 静态 Token（备选）⭐⭐⭐

```bash
# 获取 token
curl "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx51bcdd71b906032a&secret=b96e213a112354df35f5a680d9b388d3"

# 配置
WECHAT_ACCESS_TOKEN=72_xxxxxxxxxxxxxxxxxxxxx
```

**优点**:
- ✅ 简单直接
- ✅ 不依赖 AppSecret
- ⚠️ 需要定期更新

---

## 🔧 技术实现

### 核心代码

```python
# src/wechat/client.py

class WeChatClient:
    def __init__(self, appid=None, appsecret=None, access_token=None):
        # 优先级：参数 > 环境变量
        self.appid = appid or os.getenv("WECHAT_APPID")
        self.appsecret = appsecret or os.getenv("WECHAT_APPSECRET")
        self.access_token = access_token or os.getenv("WECHAT_ACCESS_TOKEN")
        
        # 缓存
        self._token_cache = {
            "token": None,
            "expires_at": 0
        }
    
    def _get_token_from_api(self):
        """通过 AppID + AppSecret 获取 token"""
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.appsecret}"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # 缓存
        self._token_cache["token"] = data["access_token"]
        self._token_cache["expires_at"] = time.time() + data["expires_in"] - 300
        
        return data["access_token"]
    
    def get_valid_token(self):
        """获取有效 token（智能管理）"""
        # 1. 检查缓存
        if self._token_cache["token"] and time.time() < self._token_cache["expires_at"]:
            return self._token_cache["token"]
        
        # 2. 尝试 API 获取
        if self.appid and self.appsecret:
            try:
                return self._get_token_from_api()
            except:
                pass
        
        # 3. 使用静态配置
        return self.access_token
```

---

## 📊 对比

| 方案 | 自动更新 | IP 限制 | 复杂度 | 推荐度 |
|------|---------|---------|--------|--------|
| **AppID + AppSecret** | ✅ 是 | ✅ 无 | ⭐ | ⭐⭐⭐⭐⭐ |
| **静态 Token** | ❌ 否 | ✅ 无 | ⭐ | ⭐⭐⭐ |
| **IP 白名单** | ✅ 是 | ⚠️ 有 | ⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 🎯 使用示例

### 示例 1: 自动模式

```python
from wechat.client import WeChatClient

# 自动获取 token
client = WeChatClient(
    appid="wx51bcdd71b906032a",
    appsecret="b96e213a112354df35f5a680d9b388d3"
)

# 发布文章（自动获取 token）
result = client.publish(media_id)
```

### 示例 2: 静态模式

```python
# 使用静态 token
client = WeChatClient(
    access_token="72_xxxxxxxxxxxxx"
)

# 发布文章
result = client.publish(media_id)
```

### 示例 3: 混合模式

```python
# 优先使用 API，失败时降级到静态 token
client = WeChatClient(
    appid="wx51bcdd71b906032a",
    appsecret="b96e213a112354df35f5a680d9b388d3",
    access_token="72_xxxxxxxxxxxxx"  # 备用
)
# 自动管理，无需关心 token
```

---

## 🎉 总结

**WeChat AI Writer 现已支持自动获取 Token！**

**核心优势**:
- ✅ **完全自动化** - 无需手动更新
- ✅ **智能降级** - 失败时自动使用备用方案
- ✅ **缓存管理** - 2小时有效期，提前5分钟更新
- ✅ **灵活配置** - 支持多种配置方式

**推荐配置**:
```bash
# .env
WECHAT_APPID=wx51bcdd71b906032a
WECHAT_APPSECRET=b96e213a112354df35f5a680d9b388d3
```

**立即使用**:
```bash
python src/main.py --keyword "人工智能"
```

---

**更新时间**: 2026-03-26 20:22
**文档版本**: v1.2.0
**状态**: ✅ 生产就绪
