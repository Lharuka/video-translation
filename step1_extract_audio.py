#!/usr/bin/env python3
"""
步骤1：从视频提取音频（16kHz 单声道 wav）

用法:
  python step1_extract_audio.py raw/sample.mp4
  python step1_extract_audio.py              # 自动处理 raw/ 下第一个 mp4
"""

import sys
import subprocess
from pathlib import Path

RAW_DIR = Path("raw")
TEMP_DIR = Path("temp")


def run(cmd, **kwargs):
    print(f">>> {' '.join(cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def extract_audio(video_path: Path, audio_path: Path):
    run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000",
        str(audio_path)
    ], capture_output=True)
    print(f"[音频提取完成] -> {audio_path}")


def main():
    if len(sys.argv) >= 2:
        video_path = Path(sys.argv[1])
    else:
        video_path = next(RAW_DIR.glob("*.mp4"), None)
        if video_path is None:
            print("用法: python step1_extract_audio.py raw/xxx.mp4")
            sys.exit(1)

    work_temp = TEMP_DIR / video_path.stem
    work_temp.mkdir(parents=True, exist_ok=True)
    audio_path = work_temp / "audio.wav"

    print(f"处理: {video_path}")
    extract_audio(video_path, audio_path)


if __name__ == "__main__":
    main()
