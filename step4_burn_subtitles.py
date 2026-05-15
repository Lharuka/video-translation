#!/usr/bin/env python3
"""
步骤4：将字幕硬编码到视频画面（ffmpeg）

用法:
  python step4_burn_subtitles.py raw/sample.mp4
  python step4_burn_subtitles.py              # 自动处理 raw/ 下第一个 mp4
"""

import sys
import subprocess
from pathlib import Path

RAW_DIR = Path("raw")
OUTPUT_DIR = Path("output")


def run(cmd, **kwargs):
    print(f">>> {' '.join(cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def burn_subtitles(video_path: Path, srt_path: Path, out_path: Path):
    srt_str = str(srt_path).replace("\\", "/")
    vf = f"subtitles='{srt_str}'"
    run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", vf,
        "-c:a", "copy",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        str(out_path)
    ], capture_output=True)
    print(f"[烧录完成] -> {out_path}")


def main():
    if len(sys.argv) >= 2:
        video_path = Path(sys.argv[1])
    else:
        video_path = next(RAW_DIR.glob("*.mp4"), None)
        if video_path is None:
            print("用法: python step4_burn_subtitles.py raw/xxx.mp4")
            sys.exit(1)

    work_output = OUTPUT_DIR / video_path.stem
    srt_path = work_output / f"{video_path.stem}_zh.srt"
    if not srt_path.exists():
        print(f"错误: 未找到字幕文件 {srt_path}，请先运行 step3_translate.py")
        sys.exit(1)

    video_out = work_output / f"{video_path.stem}_zh.mp4"

    print(f"烧录字幕: {srt_path} -> {video_out}")
    burn_subtitles(video_path, srt_path, video_out)


if __name__ == "__main__":
    main()
