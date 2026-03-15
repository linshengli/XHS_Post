#!/bin/bash
#
# run_daily_pipeline.sh - 小红书笔记每日自动生成脚本（支持任意主题 + 多账号）
#
# 用法:
#   ./run_daily_pipeline.sh                          # 默认主题 + 单账号
#   ./run_daily_pipeline.sh "主题关键词"              # 指定主题 + 单账号
#   ./run_daily_pipeline.sh "主题关键词" multi        # 多账号模式
#
# 示例:
#   ./run_daily_pipeline.sh "千岛湖亲子酒店"           # 单账号
#   ./run_daily_pipeline.sh "千岛湖亲子酒店" multi     # 多账号差异化
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 路径配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="${XHS_POST_BASE_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
SCRIPTS_DIR="$BASE_DIR/scripts"
CONFIG_DIR="$BASE_DIR/config"
LOG_FILE="$BASE_DIR/logs/pipeline_$(date +%Y-%m-%d_%H%M%S).log"

# 默认主题
DEFAULT_TOPIC="千岛湖亲子酒店"
TOPIC=${1:-"$DEFAULT_TOPIC"}
MODE=${2:-"single"}  # single 或 multi

# 创建日志目录
mkdir -p "$BASE_DIR/logs"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 主函数
main() {
    echo "============================================================"
    echo "🚀 小红书笔记自动生成系统 - 通用主题模式"
    echo "📅 执行日期：$(date '+%Y-%m-%d %H:%M:%S')"
    echo "🎯 生成主题：$TOPIC"
    echo "============================================================"
    echo ""
    
    # 检查 Python 环境
    print_info "检查 Python 环境..."
    if ! command -v python3 &> /dev/null; then
        print_error "未找到 Python3，请先安装 Python3"
        exit 1
    fi
    print_success "Python 环境就绪"
    
    # 切换到工作目录
    cd "$BASE_DIR"
    print_info "工作目录：$BASE_DIR"
    echo ""
    
    echo "============================================================"
    print_info "通过统一 CLI 执行主流程"
    echo "============================================================"
    if [ -f "$SCRIPTS_DIR/xhs_cli.py" ]; then
        if [ "$MODE" = "multi" ]; then
            XHS_POST_BASE_DIR="$BASE_DIR" python3 "$SCRIPTS_DIR/03_multi_account_orchestrator.py" --topic "$TOPIC" 2>&1 | tee -a "$LOG_FILE"
        else
            XHS_POST_BASE_DIR="$BASE_DIR" python3 "$SCRIPTS_DIR/xhs_cli.py" release-candidate --topic "$TOPIC" --count 10 2>&1 | tee -a "$LOG_FILE"
        fi
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            print_error "主流程执行失败"
            exit 1
        fi
    else
        print_error "脚本不存在：xhs_cli.py"
        exit 1
    fi
    echo ""
    
    # 完成
    echo "============================================================"
    print_success "✅ 今日 10 篇笔记生成完成！"
    echo "============================================================"
    echo ""
    print_info "🎯 主题：$TOPIC"
    print_info "📂 输出目录：$BASE_DIR/generated_posts/$(date +%Y-%m-%d)/"
    print_info "📄 日志文件：$LOG_FILE"
    echo ""
    print_info "💡 提示："
    print_info "   • 更换主题：./run_daily_pipeline.sh \"新主题\""
    print_info "   • 多账号模式：./run_daily_pipeline.sh \"主题\" multi"
    print_info "   • 设置 cron 定时任务：0 6 * * * $SCRIPTS_DIR/run_daily_pipeline.sh \"主题\" multi"
    echo ""
}

# 执行主函数
main "$@"
