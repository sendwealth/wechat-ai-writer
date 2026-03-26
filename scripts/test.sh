#!/bin/bash
# 测试脚本

set -e

echo "🧪 WeChat AI Writer - 测试运行"
echo "="*60

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 bash scripts/setup.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，创建测试配置..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件"
    echo ""
    echo "⚠️  当前使用测试配置，API 调用可能失败"
    echo "   请编辑 .env 文件，填入你的 API Keys"
    echo ""
fi

# 运行测试
echo "📝 运行测试（关键词：人工智能）"
echo ""

python src/main.py --keyword "人工智能" --dry-run

echo ""
echo "="*60
echo "✅ 测试完成"
echo "="*60
