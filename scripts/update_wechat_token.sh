#!/bin/bash
# 微信 Access Token 更新脚本

set -e

# 配置 - 请填入你的实际值
APPID="你的AppID"
SECRET="你的AppSecret"
ENV_FILE="$(dirname "$0")/../.env"

echo "🔄 更新微信 Access Token"
echo "="*60

# 检查依赖
if ! command -v jq &> /dev/null; then
    echo "❌ 未安装 jq，请先安装: brew install jq"
    exit 1
fi

# 获取 token
echo "📡 正在获取 Access Token..."
RESPONSE=$(curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=$APPID&secret=$SECRET")

# 解析 token
TOKEN=$(echo "$RESPONSE" | jq -r '.access_token')
EXPIRES_IN=$(echo "$RESPONSE" | jq -r '.expires_in')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo "✅ Token 获取成功"
    echo "   Token: ${TOKEN:0:30}..."
    echo "   有效期: $EXPIRES_IN 秒"
    
    # 更新 .env
    if [ -f "$ENV_FILE" ]; then
        # 检查是否已存在
        if grep -q "WECHAT_ACCESS_TOKEN=" "$ENV_FILE"; then
            # 更新
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/WECHAT_ACCESS_TOKEN=.*/WECHAT_ACCESS_TOKEN=$TOKEN/" "$ENV_FILE"
            else
                # Linux
                sed -i "s/WECHAT_ACCESS_TOKEN=.*/WECHAT_ACCESS_TOKEN=$TOKEN/" "$ENV_FILE"
            fi
            echo "✅ .env 文件已更新"
        else
            # 添加
            echo "" >> "$ENV_FILE"
            echo "# WeChat Access Token (自动更新于 $(date))" >> "$ENV_FILE"
            echo "WECHAT_ACCESS_TOKEN=$TOKEN" >> "$ENV_FILE"
            echo "✅ .env 文件已添加"
        fi
    else
        echo "⚠️  .env 文件不存在"
    fi
    
    echo "="*60
    echo "✅ 更新完成"
    echo "="*60
else
    ERROR=$(echo "$RESPONSE" | jq -r '.errmsg // "未知错误"')
    echo "❌ Token 获取失败: $ERROR"
    echo "   响应: $RESPONSE"
    exit 1
fi
