#!/bin/bash
# WeChat AI Writer - 每日自动发布脚本

# 进入项目目录
cd /root/.openclaw/workspace/wechat-ai-writer

# 激活虚拟环境
source venv/bin/activate

# 生成今日关键词（可根据需要修改）
KEYWORDS=("AI技术" "人工智能" "机器学习" "深度学习" "大模型" "科技新闻" "数字化转型")
RANDOM_INDEX=$((RANDOM % ${#KEYWORDS[@]}))
KEYWORD=${KEYWORDS[$RANDOM_INDEX]}

# 记录日志
echo "========================================" >> logs/cron.log
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始执行每日发布" >> logs/cron.log
echo "关键词: $KEYWORD" >> logs/cron.log

# 运行工作流（正式发布）
python src/main.py --keyword "$KEYWORD" >> logs/cron.log 2>&1

# 记录完成
echo "$(date '+%Y-%m-%d %H:%M:%S') - 发布完成" >> logs/cron.log
echo "========================================" >> logs/cron.log
