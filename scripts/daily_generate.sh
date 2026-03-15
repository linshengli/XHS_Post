#!/bin/bash
# 小红书笔记每日自动生成脚本
# 用法：./scripts/daily_generate.sh "亲子酒店" 8

TOPIC=${1:-"亲子酒店"}
COUNT=${2:-8}

echo "========================================"
echo "📝 小红书笔记每日自动生成"
echo "========================================"
echo "主题：$TOPIC"
echo "数量：$COUNT 篇"
echo "日期：$(date +%Y-%m-%d)"
echo "========================================"
echo ""

cd ~/XHS_Post

# Step 1: 分析热点数据
echo "📂 Step 1: 分析热点数据..."
python3 scripts/02_analyze_trending.py --topic "$TOPIC"
if [ $? -ne 0 ]; then
    echo "❌ 热点分析失败"
    exit 1
fi
echo ""

# Step 2: 生成笔记
echo "🤖 Step 2: 生成原创笔记..."
python3 scripts/generate_posts_llm.py --topic "$TOPIC" --count $COUNT --clean-old
if [ $? -ne 0 ]; then
    echo "❌ 笔记生成失败"
    exit 1
fi
echo ""

# Step 3: 显示结果
echo "📊 Step 3: 生成结果"
echo "========================================"
ls -lh generated_posts/$(date +%Y-%m-%d)/${TOPIC}_*.md 2>/dev/null || echo "❌ 未找到生成的文件"
echo "========================================"
echo ""
echo "✅ 完成！"
