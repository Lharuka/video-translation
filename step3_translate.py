#!/usr/bin/env python3
"""
步骤3：LLM 翻译字幕（Kimi）
只上传听写纯文本，流式输出翻译过程，最后与时间轴重组生成 SRT。

用法:
  python step3_translate.py raw/sample.mp4
  python step3_translate.py              # 自动处理 raw/ 下第一个 mp4
"""

import os
import sys
from pathlib import Path
from openai import OpenAI
import srt

LLM_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
LLM_BASE_URL = "https://api.moonshot.cn/v1"
LLM_MODEL = os.getenv("LLM_MODEL", "kimi-k2.6")
THINKING_MODE = os.getenv("THINKING_MODE", "disabled")

TRANSLATE_PROMPT = (
    "你将收到一段视频的字幕文本，每行是一句原文。"
    "请逐行翻译成中文，保持总行数与原完全一致，不要合并或拆分句子。"
    "文本由 Whisper 模型生成，可能有错误，允许你纠错。"
    "直接返回翻译后的文本，每行一句，不要添加任何解释、编号或 markdown 格式。"
)

TEMP_DIR = Path("temp")
OUTPUT_DIR = Path("output")
RAW_DIR = Path("raw")


def translate_text(text_lines: list[str], raw_path: Path) -> list[str]:
    """调用 Kimi API 逐行翻译纯文本（流式输出）。"""
    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    input_text = "\n".join(text_lines)

    extra_body = {}
    if THINKING_MODE == "disabled":
        extra_body["thinking"] = {"type": "disabled"}
    else:
        extra_body["thinking"] = {"type": "enabled"}

    stream = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": TRANSLATE_PROMPT},
            {"role": "user", "content": input_text},
        ],
        extra_body=extra_body,
        stream=True,
    )

    content_parts = []
    reasoning_parts = []

    print("\n" + "=" * 50)
    print("LLM 流式输出开始")
    print("=" * 50 + "\n")

    for chunk in stream:
        delta = chunk.choices[0].delta
        # 思考过程
        reasoning = getattr(delta, "reasoning_content", None)
        if reasoning:
            reasoning_parts.append(reasoning)
            print(reasoning, end="", flush=True)
        # 正式输出
        if delta.content:
            content_parts.append(delta.content)
            print(delta.content, end="", flush=True)

    print("\n\n" + "=" * 50)
    print("LLM 输出结束")
    print("=" * 50)

    # 保存完整原始输出到 temp（Markdown 格式）
    md_lines = [f"# LLM 原始输出\n"]
    if reasoning_parts:
        md_lines.append("## 思考过程\n")
        md_lines.append("".join(reasoning_parts))
        md_lines.append("\n\n---\n")
    md_lines.append("## 正式输出\n")
    md_lines.append("".join(content_parts))
    raw_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\n[原始输出已保存] -> {raw_path}")

    # 解析正式输出为逐行译文
    translated = "".join(content_parts).strip()
    translated = translated.replace("```", "").strip()
    output_lines = [line.strip() for line in translated.splitlines() if line.strip()]

    # 行数校验
    if len(output_lines) != len(text_lines):
        print(f"[!] 警告: 译文行数({len(output_lines)})与原文字数({len(text_lines)})不一致，尝试对齐...")
        if len(output_lines) < len(text_lines):
            output_lines += [""] * (len(text_lines) - len(output_lines))
        else:
            output_lines = output_lines[:len(text_lines)]

    return output_lines


def build_srt(subs: list, translated_lines: list[str], dst_srt: Path):
    """将译文映射回原时间轴生成 SRT。"""
    new_subs = []
    for idx, (sub, text) in enumerate(zip(subs, translated_lines), 1):
        new_sub = srt.Subtitle(
            index=idx,
            start=sub.start,
            end=sub.end,
            content=text,
        )
        new_subs.append(new_sub)
    dst_srt.write_text(srt.compose(new_subs), encoding="utf-8")
    print(f"[翻译完成] -> {dst_srt}")


def main():
    if not LLM_API_KEY:
        print("错误: 请设置环境变量 MOONSHOT_API_KEY")
        sys.exit(1)

    if len(sys.argv) >= 2:
        video_path = Path(sys.argv[1])
    else:
        video_path = next(RAW_DIR.glob("*.mp4"), None)
        if video_path is None:
            print("用法: python step3_translate.py raw/xxx.mp4")
            sys.exit(1)

    work_output = OUTPUT_DIR / video_path.stem
    src_srt = work_output / f"{video_path.stem}_src.srt"
    if not src_srt.exists():
        print(f"错误: 未找到字幕文件 {src_srt}，请先运行 step2_transcribe.py")
        sys.exit(1)

    work_temp = TEMP_DIR / video_path.stem
    work_temp.mkdir(parents=True, exist_ok=True)
    dst_srt = work_output / f"{video_path.stem}_zh.srt"
    raw_path = work_temp / f"{video_path.stem}_llm_raw.md"

    # 解析原 SRT，提取纯文本
    subs = list(srt.parse(src_srt.read_text(encoding="utf-8")))
    text_lines = [sub.content.strip() for sub in subs]
    print(f"共 {len(text_lines)} 句，准备翻译...")

    # 调用 LLM 翻译纯文本（流式）
    translated_lines = translate_text(text_lines, raw_path)

    # 映射时间轴生成新 SRT
    build_srt(subs, translated_lines, dst_srt)


if __name__ == "__main__":
    main()
