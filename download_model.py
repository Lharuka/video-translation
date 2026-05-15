#!/usr/bin/env python3
"""
预下载 faster-whisper 模型到 models/ 目录（带显式进度条）
用法:
  python download_model.py
  python download_model.py small   # 下载指定大小模型
"""

import os
import sys

from huggingface_hub import snapshot_download

MODEL_SIZE = sys.argv[1] if len(sys.argv) > 1 else "medium"
MODEL_ID = f"Systran/faster-whisper-{MODEL_SIZE}"
CACHE_DIR = "models"

print(f"模型: {MODEL_ID}")
print(f"缓存目录: {CACHE_DIR}/")
print("开始下载...\n")

try:
    snapshot_download(
        repo_id=MODEL_ID,
        cache_dir=CACHE_DIR,
        resume_download=True,
    )
    print(f"\n✅ 模型 '{MODEL_SIZE}' 下载完成！")
except Exception as e:
    print(f"\n❌ 下载失败: {e}")
    sys.exit(1)
