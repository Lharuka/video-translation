#!/usr/bin/env python3
"""
AI 视频翻译工作流 - Gradio 前端

用法:
  conda activate video-trans
  python app.py
  # 浏览器自动打开 http://127.0.0.1:7860
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from datetime import datetime

import gradio as gr

RAW_DIR = Path("raw")
OUTPUT_DIR = Path("output")
TEMP_DIR = Path("temp")


def refresh_video_list():
    """获取 raw/ 目录下所有视频文件。"""
    exts = ("*.mp4", "*.mkv", "*.mov", "*.avi", "*.wmv")
    files = []
    for ext in exts:
        files.extend(sorted(RAW_DIR.glob(ext)))
    return [str(f) for f in files]


def refresh_output_info(video_path: str):
    """获取指定视频的输出文件信息（含绝对路径）。"""
    if not video_path:
        return []
    stem = Path(video_path).stem
    work_dir = OUTPUT_DIR / stem
    if not work_dir.exists():
        return []
    rows = []
    for f in sorted(work_dir.iterdir()):
        if f.is_file():
            mtime = f.stat().st_mtime
            size = f.stat().st_size
            size_str = f"{size / 1024 / 1024:.2f} MB" if size > 1024 * 1024 else f"{size / 1024:.1f} KB"
            time_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            rows.append([f.name, str(f.resolve()), time_str, size_str])
    return rows


def open_output_dir(video_path: str):
    """打开输出目录。"""
    if not video_path:
        return "请先选择视频"
    stem = Path(video_path).stem
    work_dir = OUTPUT_DIR / stem
    work_dir.mkdir(parents=True, exist_ok=True)
    try:
        if platform.system() == "Windows":
            os.startfile(str(work_dir))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(work_dir)])
        else:
            subprocess.Popen(["xdg-open", str(work_dir)])
        return f"已打开: {work_dir}"
    except Exception as e:
        return f"打开失败: {e}"


def upload_video(file_obj):
    """选择视频文件，直接使用原始路径，不复制到 raw/。"""
    if file_obj is None:
        return "未选择文件", gr.Dropdown(choices=refresh_video_list())
    src = str(file_obj)
    return f"已选择: {Path(src).name}", gr.Dropdown(
        choices=refresh_video_list() + [src],
        value=src,
    )


def set_env(asr_backend, model_size, thinking_mode):
    """设置环境变量。"""
    os.environ["ASR_BACKEND"] = asr_backend
    os.environ["WHISPER_MODEL_SIZE"] = model_size
    os.environ["THINKING_MODE"] = thinking_mode


def get_subprocess_env():
    """获取强制 UTF-8 编码 + 无缓冲的子进程环境变量。"""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    return env


def load_subtitles(video_path: str):
    """加载原始和翻译字幕内容。"""
    if not video_path:
        return "请先选择视频", "请先选择视频"
    stem = Path(video_path).stem
    src_path = OUTPUT_DIR / stem / f"{stem}_src.srt"
    zh_path = OUTPUT_DIR / stem / f"{stem}_zh.srt"
    src_text = src_path.read_text(encoding="utf-8") if src_path.exists() else "（尚未生成）"
    zh_text = zh_path.read_text(encoding="utf-8") if zh_path.exists() else "（尚未生成）"
    return src_text, zh_text


def save_subtitles(video_path: str, src_text: str, zh_text: str):
    """保存修改后的字幕，并返回刷新后的输出文件信息。"""
    if not video_path:
        return []
    stem = Path(video_path).stem
    work_dir = OUTPUT_DIR / stem
    work_dir.mkdir(parents=True, exist_ok=True)
    src_path = work_dir / f"{stem}_src.srt"
    zh_path = work_dir / f"{stem}_zh.srt"
    src_path.write_text(src_text, encoding="utf-8")
    zh_path.write_text(zh_text, encoding="utf-8")
    return refresh_output_info(video_path)


# ---------- 步骤执行（单输出 generator，日志连续） ----------

def run_step(script: str, video_path: str, asr_backend: str, model_size: str, thinking_mode: str, current_log: str):
    """运行单个步骤脚本，流式返回日志（追加到当前日志后）。"""
    if not video_path:
        yield current_log + "\n[错误] 请先选择或上传视频"
        return

    set_env(asr_backend, model_size, thinking_mode)
    cmd = [sys.executable, script, video_path]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=get_subprocess_env(),
    )

    output = [current_log, f"\n{'='*50}\n[运行] {script}\n{'='*50}\n"]
    yield "".join(output)  # 立即显示步骤标题，避免长时间空白
    for line in process.stdout:
        output.append(line)
        yield "".join(output)

    process.wait()
    if process.returncode != 0:
        output.append(f"\n[错误] {script} 返回码: {process.returncode}")
    else:
        output.append(f"\n[完成] {script}")
    yield "".join(output)


def _refresh_all(video_path: str):
    """刷新字幕编辑器和输出文件信息。"""
    src, zh = load_subtitles(video_path)
    info = refresh_output_info(video_path)
    return src, zh, info


# -------------------- Gradio 界面 --------------------
CSS = """
.fixed-log textarea {
    height: 400px !important;
    max-height: 400px !important;
    resize: none !important;
}
/* 隐藏 File 组件的文件操作按钮（下载/删除） */
.file-preview button,
.file-preview a[download],
.file-display button,
.file-display a[download],
[data-testid="file"] .file-item button,
[data-testid="file"] .file-item a[download] {
    display: none !important;
}
"""

with gr.Blocks(title="AI 视频翻译工作流") as demo:
    gr.Markdown("# 🎬 AI 视频翻译工作流")
    gr.Markdown("基于 faster-whisper + Kimi K2.6 的自动化视频字幕翻译")

    with gr.Row():
        # 左侧面板
        with gr.Column(scale=1):
            gr.Markdown("### 📤 上传视频")
            upload = gr.File(label="上传视频到 raw/", file_types=[".mp4", ".mkv", ".mov", ".avi"])
            upload_status = gr.Textbox(label="上传状态", interactive=False)

            gr.Markdown("### ⚙️ 配置")
            asr_backend = gr.Dropdown(
                choices=["local", "cloud"],
                value="local",
                label="ASR 后端",
            )
            model_size = gr.Dropdown(
                choices=["tiny", "base", "small", "medium", "large-v3"],
                value="medium",
                label="Whisper 模型",
            )
            thinking_mode = gr.Dropdown(
                choices=["enabled", "disabled"],
                value="disabled",
                label="K2.6 思考模式",
            )

            gr.Markdown("### 🎞️ 选择视频")
            video_select = gr.Dropdown(
                choices=refresh_video_list(),
                label="raw/ 中的视频",
                allow_custom_value=True,
            )
            refresh_btn = gr.Button("🔄 刷新列表")

            gr.Markdown("### ▶️ 执行步骤")
            with gr.Row():
                s1_btn = gr.Button("1️⃣ 提取音频", size="sm")
                s2_btn = gr.Button("2️⃣ 语音转写", size="sm")
            with gr.Row():
                s3_btn = gr.Button("3️⃣ 翻译字幕", size="sm")
                s4_btn = gr.Button("4️⃣ 烧录字幕", size="sm")
            run_all_btn = gr.Button("🚀 一键全部", variant="primary")

        # 右侧面板
        with gr.Column(scale=2):
            gr.Markdown("### 📋 运行日志")
            log_box = gr.Textbox(
                label="",
                lines=25,
                interactive=False,
                autoscroll=True,
                elem_classes=["fixed-log"],
            )

            gr.Markdown("### ✏️ 字幕编辑器")
            with gr.Row():
                with gr.Column():
                    src_editor = gr.Textbox(
                        label="原始字幕 (_src.srt)",
                        lines=15,
                        max_lines=15,
                        interactive=True,
                    )
                with gr.Column():
                    zh_editor = gr.Textbox(
                        label="翻译字幕 (_zh.srt)",
                        lines=15,
                        max_lines=15,
                        interactive=True,
                    )
            with gr.Row():
                load_sub_btn = gr.Button("📂 加载字幕", size="sm")
                save_sub_btn = gr.Button("💾 保存修改", variant="primary", size="sm")

            gr.Markdown("### 📁 输出文件")
            output_info = gr.Dataframe(
                headers=["文件名", "绝对路径", "修改时间", "大小"],
                label="",
                interactive=False,
            )
            with gr.Row():
                refresh_out_btn = gr.Button("🔄 刷新输出", size="sm")
                open_dir_btn = gr.Button("📂 打开输出目录", size="sm")
            open_dir_status = gr.Textbox(label="", interactive=False, visible=False)

    # ---------- 事件绑定 ----------
    upload.upload(upload_video, inputs=upload, outputs=[upload_status, video_select])
    refresh_btn.click(refresh_video_list, outputs=video_select)

    # step1：只运行，不产生字幕/输出文件
    s1_btn.click(
        run_step,
        inputs=[gr.State("step1_extract_audio.py"), video_select, asr_backend, model_size, thinking_mode, log_box],
        outputs=log_box,
    )

    # step2：运行 → 成功后刷新字幕+输出文件
    s2_event = s2_btn.click(
        run_step,
        inputs=[gr.State("step2_transcribe.py"), video_select, asr_backend, model_size, thinking_mode, log_box],
        outputs=log_box,
    )
    s2_event.success(
        _refresh_all,
        inputs=video_select,
        outputs=[src_editor, zh_editor, output_info],
    )

    # step3：运行 → 成功后刷新字幕+输出文件
    s3_event = s3_btn.click(
        run_step,
        inputs=[gr.State("step3_translate.py"), video_select, asr_backend, model_size, thinking_mode, log_box],
        outputs=log_box,
    )
    s3_event.success(
        _refresh_all,
        inputs=video_select,
        outputs=[src_editor, zh_editor, output_info],
    )

    # step4：运行 → 成功后只刷新输出文件（不产生字幕）
    s4_event = s4_btn.click(
        run_step,
        inputs=[gr.State("step4_burn_subtitles.py"), video_select, asr_backend, model_size, thinking_mode, log_box],
        outputs=log_box,
    )
    s4_event.success(
        refresh_output_info,
        inputs=video_select,
        outputs=output_info,
    )

    # 一键全部：step1 → step2 → 刷新 → step3 → 刷新 → step4 → 刷新输出
    e1 = run_all_btn.click(
        run_step,
        inputs=[gr.State("step1_extract_audio.py"), video_select, asr_backend, model_size, thinking_mode, log_box],
        outputs=log_box,
    )
    e2 = e1.success(
        run_step,
        inputs=[gr.State("step2_transcribe.py"), video_select, asr_backend, model_size, thinking_mode, log_box],
        outputs=log_box,
    )
    e2.success(
        _refresh_all,
        inputs=video_select,
        outputs=[src_editor, zh_editor, output_info],
    )
    e3 = e2.success(
        run_step,
        inputs=[gr.State("step3_translate.py"), video_select, asr_backend, model_size, thinking_mode, log_box],
        outputs=log_box,
    )
    e3.success(
        _refresh_all,
        inputs=video_select,
        outputs=[src_editor, zh_editor, output_info],
    )
    e4 = e3.success(
        run_step,
        inputs=[gr.State("step4_burn_subtitles.py"), video_select, asr_backend, model_size, thinking_mode, log_box],
        outputs=log_box,
    )
    e4.success(
        refresh_output_info,
        inputs=video_select,
        outputs=output_info,
    )

    # 字幕编辑
    load_sub_btn.click(load_subtitles, inputs=video_select, outputs=[src_editor, zh_editor])
    save_sub_btn.click(save_subtitles, inputs=[video_select, src_editor, zh_editor], outputs=output_info)

    # 输出文件
    refresh_out_btn.click(refresh_output_info, inputs=video_select, outputs=output_info)
    open_dir_btn.click(open_output_dir, inputs=video_select, outputs=open_dir_status)

if __name__ == "__main__":
    RAW_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)
    demo.launch(share=False, inbrowser=True, css=CSS)
