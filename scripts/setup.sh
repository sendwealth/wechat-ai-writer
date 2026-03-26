#!/bin/bash
# 环境配置脚本

set -e

echo "🚀 WeChat AI Writer - 环境配置"
echo "="*60

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未安装 Python3"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 配置环境变量
if [ ! -f ".env" ]; then
    echo "⚙️  配置环境变量..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请填写你的 API Keys"
else
    echo "✅ .env 文件已存在"
fi

# 创建目录
echo "📁 创建目录..."
mkdir -p logs outputs

echo "="*60
echo "✅ 环境配置完成！"
echo ""
echo "下一步："
echo "1. 编辑 .env 文件，填写你的 API Keys"
echo "2. 运行测试: python src/main.py --keyword '人工智能' --dry-run"
echo "3. 启动服务: python src/main.py --server --port 5000"
echo "="*60
