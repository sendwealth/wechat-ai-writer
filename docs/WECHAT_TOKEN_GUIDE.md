# 微信 Access Token 获取指南

## ⚠️ IP 白名单问题

**问题**: 微信公众号 API 有 IP 白名单限制，必须配置服务器 IP 才能获取 Access Token。

**影响**:
- 动态 IP 无法使用 AppID + AppSecret 获取 Token
- 服务器 IP 变化后需要重新配置
- 本地开发环境难以测试

---

## 🎯 解决方案

### 方案1: 直接使用 Access Token（推荐）⭐⭐⭐⭐⭐

**适用场景**: 
- 本地开发测试
- IP 经常变化
- 简单快速

**步骤**:

#### 1. 通过浏览器获取

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

#### 2. 使用命令行

```bash
curl "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=你的AppID&secret=你的AppSecret"
```

#### 3. 使用 Python

```python
import requests

appid = "你的AppID"
appsecret = "你的AppSecret"

url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
response = requests.get(url)
data = response.json()

print(f"Access Token: {data['access_token']}")
print(f"有效期: {data['expires_in']} 秒")
```

#### 4. 配置到项目

```bash
# .env 文件
WECHAT_ACCESS_TOKEN=72_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**优点**:
- ✅ 不受 IP 限制
- ✅ 简单快速
- ✅ 适合本地开发

**缺点**:
- ⚠️ 2小时过期，需要定期更新
- ⚠️ 需要手动操作

---

### 方案2: 自动更新 Access Token

**适用场景**: 
- 长期运行的服务
- 需要自动化管理

**实现**:

```python
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

class WeChatTokenManager:
    def __init__(self, appid, appsecret):
        self.appid = appid
        self.appsecret = appsecret
        self.token = None
        self.expires_at = 0
    
    def get_token(self):
        """获取有效的 access_token"""
        if self.token and time.time() < self.expires_at:
            return self.token
        
        # 重新获取
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.appsecret}"
        
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if "errcode" in data:
                raise Exception(f"获取 access_token 失败: {data.get('errmsg')}")
            
            self.token = data["access_token"]
            self.expires_at = time.time() + data["expires_in"] - 300  # 提前5分钟过期
            
            # 更新环境变量
            os.environ["WECHAT_ACCESS_TOKEN"] = self.token
            
            return self.token
        except Exception as e:
            print(f"更新 access_token 失败: {e}")
            return None
    
    def auto_refresh(self, interval=7000):
        """自动刷新（每7000秒 = 约2小时）"""
        while True:
            self.get_token()
            time.sleep(interval)

# 使用示例
if __name__ == "__main__":
    manager = WeChatTokenManager(
        appid="你的AppID",
        appsecret="你的AppSecret"
    )
    
    # 获取 token
    token = manager.get_token()
    print(f"Access Token: {token}")
    
    # 自动刷新（后台运行）
    # manager.auto_refresh()
```

**优点**:
- ✅ 自动更新
- ✅ 无需手动操作
- ✅ 提前过期机制

**缺点**:
- ⚠️ 需要配置 IP 白名单
- ⚠️ 需要后台运行

---

### 方案3: 配置 IP 白名单

**适用场景**: 
- 固定 IP 服务器
- 生产环境

**步骤**:

#### 1. 登录微信公众平台

访问: https://mp.weixin.qq.com/

#### 2. 配置 IP 白名单

路径: **设置与开发** → **基本配置** → **IP白名单**

#### 3. 添加服务器 IP

```
# 查看你的公网 IP
curl ifconfig.me

# 或
curl ip.sb
```

#### 4. 使用 AppID + AppSecret

```python
import requests

appid = "你的AppID"
appsecret = "你的AppSecret"

url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
response = requests.get(url)
data = response.json()

print(f"Access Token: {data['access_token']}")
```

**优点**:
- ✅ 官方推荐方式
- ✅ 自动获取 Token
- ✅ 安全性高

**缺点**:
- ⚠️ 必须固定 IP
- ⚠️ 配置较繁琐

---

### 方案4: 使用代理服务器

**适用场景**: 
- 无固定 IP
- 需要稳定访问

**架构**:
```
本地开发 → 代理服务器（固定IP）→ 微信API
```

**实现**:

```python
import requests

# 使用代理
proxies = {
    "http": "http://your-proxy-ip:port",
    "https": "http://your-proxy-ip:port"
}

url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
response = requests.get(url, proxies=proxies)
```

**优点**:
- ✅ 解决 IP 限制
- ✅ 本地可用

**缺点**:
- ⚠️ 需要代理服务器
- ⚠️ 增加成本

---

## 🎯 推荐方案

### 本地开发 → **方案1**（直接使用 Token）

**理由**:
- ✅ 简单快速
- ✅ 不受 IP 限制
- ✅ 适合测试

### 生产环境 → **方案3**（IP 白名单）

**理由**:
- ✅ 官方推荐
- ✅ 安全性高
- ✅ 自动管理

---

## 📝 完整示例

### 1. 获取 Access Token

```bash
# 方法1: 浏览器访问
https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wxXXXXXXXX&secret=your_secret

# 方法2: 命令行
curl "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wxXXXXXXXX&secret=your_secret"

# 方法3: Python
python3 -c "
import requests, os
from dotenv import load_dotenv
load_dotenv()
appid = os.getenv('WECHAT_APPID')
secret = os.getenv('WECHAT_APPSECRET')
r = requests.get(f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}')
print(r.json())
"
```

### 2. 配置到项目

```bash
# 编辑 .env
vim ~/clawd/projects/wechat-ai-writer/.env

# 添加
WECHAT_ACCESS_TOKEN=72_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 测试运行

```bash
cd ~/clawd/projects/wechat-ai-writer
source venv/bin/activate

# 测试模式（不发布）
python src/main.py --keyword "人工智能" --dry-run

# 正式发布
python src/main.py --keyword "人工智能"
```

---

## ⚠️ 重要提示

### 1. Access Token 有效期

- **有效期**: 2小时（7200秒）
- **建议**: 提前5分钟更新
- **策略**: 使用定时任务自动更新

### 2. 安全性

- **不要提交到代码仓库**
- **使用环境变量**
- **定期更换 AppSecret**

### 3. 频率限制

- **获取 Token**: 无限制
- **调用 API**: 根据公众号类型不同
- **建议**: 缓存 Token，避免频繁获取

---

## 🔄 自动更新脚本

### 创建自动更新脚本

```bash
# ~/clawd/projects/wechat-ai-writer/scripts/update_wechat_token.sh
#!/bin/bash

# 配置
APPID="你的AppID"
SECRET="你的AppSecret"
ENV_FILE="$HOME/clawd/projects/wechat-ai-writer/.env"

# 获取 token
TOKEN=$(curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=$APPID&secret=$SECRET" | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    # 更新 .env
    sed -i '' "s/WECHAT_ACCESS_TOKEN=.*/WECHAT_ACCESS_TOKEN=$TOKEN/" "$ENV_FILE"
    echo "✅ Token 已更新: ${TOKEN:0:20}..."
else
    echo "❌ Token 获取失败"
fi
```

### 配置定时任务

```bash
# 每小时更新一次
crontab -e

# 添加
0 * * * * /Users/rowan/clawd/projects/wechat-ai-writer/scripts/update_wechat_token.sh
```

---

## 📚 相关文档

- **微信公众平台**: https://mp.weixin.qq.com/
- **开发文档**: https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Get_access_token.html
- **IP白名单**: https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Get_access_token.html

---

## 🎉 总结

### 快速上手

1. **获取 Token**:
   ```bash
   curl "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=你的AppID&secret=你的AppSecret"
   ```

2. **配置 .env**:
   ```bash
   WECHAT_ACCESS_TOKEN=72_xxx...
   ```

3. **运行项目**:
   ```bash
   python src/main.py --keyword "人工智能" --dry-run
   ```

### 推荐方案

- **本地开发**: 直接使用 Access Token
- **生产环境**: 配置 IP 白名单 + 自动更新

---

**文档创建时间**: 2026-03-26 20:15
**适用版本**: WeChat AI Writer v1.1.0+
