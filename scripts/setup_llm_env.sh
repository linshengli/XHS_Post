#!/bin/bash
# XHS_Post LLM 配置脚本
# 从 OpenClaw 配置中读取 API key 并设置环境变量

# 读取 OpenClaw 配置中的 Bailian API key
OPENCLAW_CONFIG="$HOME/.openclaw/openclaw.json"

if [ -f "$OPENCLAW_CONFIG" ]; then
    # 提取 Bailian API key
    BAILIAN_KEY=$(cat "$OPENCLAW_CONFIG" | grep -o '"apiKey": "[^"]*"' | head -1 | sed 's/"apiKey": "//;s/"//')
    
    if [ -n "$BAILIAN_KEY" ]; then
        export BAILIAN_API_KEY="$BAILIAN_KEY"
        export XHS_POST_LLM_PROVIDER="qwen"
        export QWEN_MODEL="qwen3.5-plus"
        export BAILIAN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        echo "✅ LLM 配置完成"
        echo "   Provider: qwen"
        echo "   Model: qwen3.5-plus"
        echo "   API Key: ${BAILIAN_KEY:0:10}..."
    else
        echo "❌ 未找到 Bailian API key"
        exit 1
    fi
else
    echo "❌ 未找到 OpenClaw 配置文件: $OPENCLAW_CONFIG"
    exit 1
fi