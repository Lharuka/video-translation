#!/usr/bin/env python3
"""
一键运行完整工作流（串联 4 个步骤）

用法:
  python run_all.py raw/sample.mp4
  python run_all.py              # 自动处理 raw/ 下第一个 mp4
"""

import sys
import subprocess
from pathlib import Path

RAW_DIR = Path("raw")


def run_step(script: str, video_path: Path):
    print(f"\n{'='*50}")
    print(f"运行: {script}")
    print(f"{'='*50}")
    result = subprocess.run([sys.executable, script, str(video_path)])
    if result.returncode != 0:
        print(f"\n[!] {script} 执行失败，中断工作流。")
        sys.exit(1)


def main():
    if len(sys.argv) >= 2:
        video_path = Path(sys.argv[1])
    else:
        video_path = next(RAW_DIR.glob("*.mp4"), None)
        if video_path is None:
            print("用法: python run_all.py raw/xxx.mp4")
            sys.exit(1)

    print(f"目标视频: {video_path}")

    run_step("step1_extract_audio.py", video_path)
    run_step("step2_transcribe.py", video_path)
    run_step("step3_translate.py", video_path)
    run_step("step4_burn_subtitles.py", video_path)

    stem = video_path.stem
    print(f"\n{'='*50}")
    print("全部步骤执行完毕！")
    print(f"{'='*50}")
    print(f"temp/{stem}/")
    print(f"  - audio.wav")
    print(f"  - {stem}_llm_raw.md")
    print(f"output/{stem}/")
    print(f"  - {stem}_src.srt     (原文)")
    print(f"  - {stem}_zh.srt      (译文)")
    print(f"  - {stem}_zh.mp4      (带字幕视频)")


if __name__ == "__main__":
    main()
