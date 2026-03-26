# WeChat AI Writer - IP 限制解决方案

## 🚨 问题说明

**微信 IP 白名单限制**: 微信公众号 API 要求配置服务器 IP 白名单才能获取 Access Token。

**影响**:
- ❌ 本地开发环境（动态 IP）
- ❌ 云服务器（IP 可能变化）
- ❌ CI/CD 环境

---

## 🎯 解决方案对比

| 方案 | 适用场景 | IP 限制 | 难度 | 推荐度 |
|------|---------|--------|------|--------|
| **直接使用 Token** | 本地开发 | ✅ 无 | ⭐ | ⭐⭐⭐⭐⭐ |
| **IP 白名单** | 生产环境 | ⚠️ 有 | ⭐⭐ | ⭐⭐⭐⭐ |
| **代理服务器** | 企业环境 | ✅ 无 | ⭐⭐⭐ | ⭐⭐⭐ |
| **自动更新** | 长期运行 | ⚠️ 有 | ⭐⭐ | ⭐⭐⭐⭐ |

---

## 📝 推荐方案：直接使用 Access Token

### 为什么推荐？

1. ✅ **不受 IP 限制** - 直接使用 Token，无需 IP 白名单
2. ✅ **简单快速** - 一次获取，2小时有效
3. ✅ **本地友好** - 适合开发测试
4. ✅ **易于理解** - 无需复杂配置

### 具体步骤

#### 1. 获取 AppID 和 AppSecret

**路径**: 微信公众平台 → 设置与开发 → 基本配置

**注意**: AppSecret 只显示一次，请妥善保存

#### 2. 获取 Access Token

**方法1: 浏览器（最简单）**

```
https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=你的AppID&secret=你的AppSecret
```

**示例**:
```
https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx51bcdd71b906032a&secret=b96e213a112354df35f5a680d9b388d3
```

**返回**:
```json
{
  "access_token": "72_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "expires_in": 7200
}
```

**方法2: 命令行**

```bash
curl "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=你的AppID&secret=你的AppSecret"
```

**方法3: 使用脚本**

```bash
cd ~/clawd/projects/wechat-ai-writer
# 编辑脚本，填入你的 AppID 和 AppSecret
vim scripts/update_wechat_token.sh

# 运行脚本
./scripts/update_wechat_token.sh
```

#### 3. 配置到项目

**编辑 .env 文件**:
```bash
vim ~/clawd/projects/wechat-ai-writer/.env

# 添加或更新
WECHAT_ACCESS_TOKEN=72_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 4. 测试运行

```bash
cd ~/clawd/projects/wechat-ai-writer
source venv/bin/activate

# 测试模式（不发布）
python src/main.py --keyword "人工智能" --dry-run
```

---

## ⏰ Token 有效期管理

### 有效期

- **时长**: 2小时（7200秒）
- **建议**: 提前5分钟更新
- **策略**: 
  - 短期使用：手动获取
  - 长期使用：定时更新

### 自动更新方案

#### 方案1: 定时脚本（推荐）

```bash
# 编辑 crontab
crontab -e

# 每小时更新一次
0 * * * * /Users/rowan/clawd/projects/wechat-ai-writer/scripts/update_wechat_token.sh >> /tmp/wechat_token.log 2>&1
```

#### 方案2: Python 自动管理

```python
import os
import time
import requests
from threading import Thread

class WeChatTokenManager:
    def __init__(self, appid, appsecret):
        self.appid = appid
        self.appsecret = appsecret
        self.token = None
        self.running = False
    
    def get_token(self):
        """获取 access_token"""
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.appsecret}"
        
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if "errcode" in data:
                print(f"❌ 获取 token 失败: {data.get('errmsg')}")
                return None
            
            self.token = data["access_token"]
            os.environ["WECHAT_ACCESS_TOKEN"] = self.token
            print(f"✅ Token 已更新: {self.token[:30]}...")
            return self.token
        except Exception as e:
            print(f"❌ 异常: {e}")
            return None
    
    def auto_refresh(self):
        """后台自动刷新"""
        self.running = True
        while self.running:
            self.get_token()
            time.sleep(7000)  # 约2小时
    
    def start(self):
        """启动自动刷新"""
        thread = Thread(target=self.auto_refresh, daemon=True)
        thread.start()
    
    def stop(self):
        """停止自动刷新"""
        self.running = False

# 使用
if __name__ == "__main__":
    manager = WeChatTokenManager(
        appid="你的AppID",
        appsecret="你的AppSecret"
    )
    
    # 启动自动刷新
    manager.start()
    
    # 主程序...
    time.sleep(10000)
```

---

## 🔒 安全建议

### 1. 保护 AppSecret

```bash
# ❌ 不要硬编码
SECRET="abc123"  # 错误

# ✅ 使用环境变量
export WECHAT_APPSECRET="abc123"
```

### 2. 不要提交到 Git

```bash
# .gitignore
.env
*.secret
*_token.txt
```

### 3. 定期更换

- **频率**: 每月或每季度
- **场景**: 
  - Token 泄露
  - 人员变动
  - 定期安全审计

---

## 🐛 常见问题

### Q1: 获取 Token 返回 40164？

**错误**:
```json
{
  "errcode": 40164,
  "errmsg": "invalid ip, not in whitelist hint: [xxx]"
}
```

**原因**: IP 不在白名单中

**解决**: 使用直接 Token 方案，不使用 AppID + AppSecret

### Q2: Token 过期了怎么办？

**错误**:
```json
{
  "errcode": 40001,
  "errmsg": "invalid credential, access_token is invalid or not latest hint"
}
```

**解决**: 
1. 重新获取 Token
2. 更新 .env 文件
3. 使用自动更新脚本

### Q3: 多久更新一次 Token？

**建议**:
- 手动使用：每次使用前检查
- 自动脚本：每小时更新
- 生产环境：每90分钟更新

### Q4: 能否缓存 Token？

**可以**:
```python
import os
import time
import json

CACHE_FILE = "/tmp/wechat_token.json"

def save_token(token, expires_in):
    """保存 token 到缓存"""
    data = {
        "token": token,
        "expires_at": time.time() + expires_in - 300  # 提前5分钟
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

def get_cached_token():
    """获取缓存的 token"""
    if not os.path.exists(CACHE_FILE):
        return None
    
    with open(CACHE_FILE, 'r') as f:
        data = json.load(f)
    
    if time.time() < data["expires_at"]:
        return data["token"]
    
    return None
```

---

## 📚 完整工作流

### 开发环境

```bash
# 1. 获取 Token（浏览器）
访问: https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=你的AppID&secret=你的AppSecret

# 2. 配置
vim ~/clawd/projects/wechat-ai-writer/.env
WECHAT_ACCESS_TOKEN=72_xxx...

# 3. 测试
python src/main.py --keyword "人工智能" --dry-run
```

### 生产环境

```bash
# 1. 配置 IP 白名单
微信公众平台 → 设置与开发 → 基本配置 → IP白名单

# 2. 配置自动更新
crontab -e
0 * * * * /path/to/update_wechat_token.sh

# 3. 运行服务
python src/main.py --server --port 5000
```

---

## 🎉 总结

### 最佳实践

1. **本地开发**: 直接使用 Token
2. **生产环境**: IP 白名单 + 自动更新
3. **安全**: 保护 AppSecret，定期更换
4. **稳定**: 定时更新，提前过期

### 快速开始

```bash
# 1. 获取 Token
curl "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=你的AppID&secret=你的AppSecret"

# 2. 配置
echo "WECHAT_ACCESS_TOKEN=72_xxx..." >> .env

# 3. 运行
python src/main.py --keyword "人工智能" --dry-run
```

---

**文档创建**: 2026-03-26 20:15
**适用版本**: WeChat AI Writer v1.1.0+
**状态**: ✅ 生产就绪
