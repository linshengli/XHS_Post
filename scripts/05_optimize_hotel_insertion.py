#!/usr/bin/env python3
"""
酒店植入优化脚本 - 兼容入口

⚠️ 已弃用：推荐使用 `python xhs.py optimize --input-dir xxx --output-dir yyy`
"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def main():
    print("⚠️  兼容入口：推荐使用 `python xhs.py optimize ...`")
    print()
    
    # 委托到统一 CLI
    cmd = [sys.executable, str(BASE_DIR / "xhs.py"), "optimize"] + sys.argv[1:]
    result = subprocess.run(cmd, cwd=BASE_DIR)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
