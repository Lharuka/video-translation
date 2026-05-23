# AI 视频翻译工作流

> 🎛️ **Vibe Coding with [Kimi Code](https://www.moonshot.cn/)** · 模型 **Kimi K2.6**

基于 **faster-whisper**（本地语音识别）+ **Kimi K2.6**（大模型翻译）的自动化视频字幕翻译工具。支持命令行分步执行和 Gradio 可视化界面，可自定义模型、校对字幕、硬编码输出。

---

## 目录

- [功能特性](#功能特性)
- [项目结构](#项目结构)
- [硬件要求](#硬件要求)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
  - [命令行模式](#命令行模式)
  - [Web 界面模式](#web-界面模式)
- [配置说明](#配置说明)
- [工作流程详解](#工作流程详解)
- [二次开发指南](#二次开发指南)
  - [替换 ASR 引擎](#替换-asr-引擎)
  - [替换翻译模型](#替换翻译模型)
  - [修改前端界面](#修改前端界面)
  - [添加新步骤](#添加新步骤)
- [常见问题](#常见问题)

---

## 功能特性

| 特性 | 说明 |
|------|------|
| **本地 ASR** | 基于 faster-whisper，支持 tiny/base/small/medium/large-v3 模型 |
| **云端 ASR 备选** | 支持硅基流动 SenseVoiceSmall（OpenAI 兼容格式） |
| **大模型翻译** | 默认 Kimi K2.6，支持思考模式纠错 |
| **字幕在线编辑** | Gradio 界面可直接修改原文和译文 |
| **自动时间轴** | 翻译时只传纯文本，时间轴由本地重组，100% 可靠 |
| **硬编码输出** | ffmpeg 将字幕烧录到视频画面 |
| **流式日志** | Web 界面实时显示每一步的终端输出 |
| **多视频隔离** | temp/ 和 output/ 下按视频名创建子目录 |

---

## 项目结构

```
.
├── raw/                          # 原始视频输入目录
├── temp/                         # 中间文件（按视频名分子目录）
│   └── {video_name}/
│       ├── audio.wav             # 提取的音频
│       └── {video_name}_llm_raw.md   # LLM 原始输出（含思考过程）
├── output/                       # 最终输出（按视频名分子目录）
│   └── {video_name}/
│       ├── {video_name}_src.srt  # 原文 SRT
│       ├── {video_name}_zh.srt   # 译文 SRT
│       └── {video_name}_zh.mp4   # 带字幕成品视频
├── models/                       # faster-whisper 模型缓存
├── app.py                        # Gradio 前端界面
├── run_all.py                    # 命令行一键执行
├── step1_extract_audio.py        # 步骤1：提取音频
├── step2_transcribe.py           # 步骤2：语音转文字
├── step3_translate.py            # 步骤3：LLM 翻译字幕
├── step4_burn_subtitles.py       # 步骤4：烧录字幕到视频
├── download_model.py             # 预下载 faster-whisper 模型
└── README.md                     # 本文件
```

---

## 硬件要求

### 最低配置
- **CPU**：任意现代多核处理器
- **内存**：8 GB
- **硬盘**：5 GB 可用空间（含模型）
- **显卡**：无显卡可用（CPU 模式）

### 推荐配置
- **CPU**：Intel i5 / AMD Ryzen 5 及以上
- **内存**：16 GB
- **显卡**：NVIDIA GTX 1650 4GB 及以上
- **硬盘**：SSD，10 GB 可用空间

### 模型显存对照（faster-whisper）

| 模型 | INT8 显存 | FP16 显存 | 速度 | 准确率 |
|------|-----------|-----------|------|--------|
| tiny | ~0.5 GB | ~1 GB | 最快 | 一般 |
| base | ~0.5 GB | ~1.5 GB | 很快 | 中等 |
| small | ~1 GB | ~2 GB | 快 | 较好 |
| medium | ~2.5 GB | **~5 GB** | 中等 | **好** |
| large-v3 | ~3.5 GB | **~10 GB** | 较慢 | **最好** |

> **建议**：4GB 显存（如 GTX 1650）推荐 `medium` + INT8；8GB 以上可尝试 `large-v3` + INT8。

---

## 快速开始

### 1. 克隆项目并创建环境

```bash
# 进入项目目录
cd video-translation

# 创建 conda 环境（Python 3.12）
conda create -n video-trans python=3.12 -y
conda activate video-trans
```

### 2. 安装依赖

```bash
pip install openai srt faster-whisper gradio
```

> `ffmpeg` 需要提前安装在系统中并加入 PATH。

**安装 ffmpeg（Windows）**：

本项目依赖 ffmpeg 进行音频提取和视频烧录。如果你尚未安装，推荐以下两种方式：

**方式一：手动安装（推荐）**

1. 从 [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 下载 `ffmpeg-release-full.7z` 或 `ffmpeg-release-full.zip`
2. 解压到任意目录，例如 `C:\Users\<用户名>\Downloads\ffmpeg-8.1.1-full_build`
3. 找到解压目录下的 `bin` 子目录（内含 `ffmpeg.exe`、`ffprobe.exe`、`ffplay.exe`）
4. 将 `bin` 目录的完整路径添加到系统环境变量 `Path` 中：

```powershell
# 以实际路径为准
$binPath = 'C:\Users\41307\Downloads\ffmpeg-8.1.1-full_build\bin'
$currentPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($currentPath -notlike "*$binPath*") {
    [Environment]::SetEnvironmentVariable('Path', "$currentPath;$binPath", 'User')
}
```

5. **新开一个 PowerShell 或终端窗口**，验证安装：

```bash
ffmpeg -version
```

**方式二：通过 winget 安装（需要管理员权限）**

```powershell
winget install Gyan.FFmpeg
```

安装完成后同样需要新开终端窗口使 PATH 生效。

### 3. 配置 API Key

在系统环境变量中配置：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `MOONSHOT_API_KEY` | Kimi API Key | `sk-xxxxxxxx` |
| `SILICONFLOW_API_KEY` | 硅基流动 API Key（可选） | `sk-xxxxxxxx` |

**Windows（PowerShell）**：
```powershell
$env:MOONSHOT_API_KEY="sk-your-key"
$env:SILICONFLOW_API_KEY="sk-your-key"
```

**Windows（永久设置）**：
在"系统属性 → 环境变量"中添加。

### 4. 下载模型（可选）

```bash
python download_model.py medium
```

模型会下载到 `models/` 目录。首次运行时若未下载，也会自动下载。

### 5. 运行

**Web 界面（推荐）**：
```bash
python app.py
# 浏览器自动打开 http://127.0.0.1:7860
```

**命令行一键执行**：
```bash
python run_all.py raw/sample.mp4
```

---

## 使用指南

### 命令行模式

将视频放入 `raw/` 目录，然后按顺序执行：

```bash
# 步骤1：提取音频
python step1_extract_audio.py raw/sample.mp4

# 步骤2：语音转写（生成原文 SRT）
python step2_transcribe.py raw/sample.mp4

# 步骤3：LLM 翻译（生成译文 SRT）
python step3_translate.py raw/sample.mp4

# 步骤4：烧录字幕到视频
python step4_burn_subtitles.py raw/sample.mp4
```

或一键执行全部：
```bash
python run_all.py raw/sample.mp4
```

### Web 界面模式

```bash
python app.py
```

界面功能：

| 区域 | 功能 |
|------|------|
| **📤 选择视频** | 拖拽或点击选择视频文件（直接使用原路径，不复制） |
| **⚙️ 配置** | 切换 ASR 后端、Whisper 模型、思考模式 |
| **🎞️ 视频列表** | 下拉选择 `raw/` 中的视频，或手动输入任意路径 |
| **▶️ 执行步骤** | 单步执行 1~4 或一键全部 |
| **📋 运行日志** | 实时流式显示终端输出 |
| **✏️ 字幕编辑器** | 在线修改原文和译文，保存后立即生效 |
| **📁 输出文件** | 显示输出目录的文件列表、绝对路径、修改时间、大小 |

---

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MOONSHOT_API_KEY` | — | **必填**，Kimi API Key |
| `MOONSHOT_API_KEY` | `https://api.moonshot.cn/v1` | Kimi Base URL |
| `LLM_MODEL` | `kimi-k2.6` | 翻译模型 |
| `THINKING_MODE` | `disabled` | `enabled` 开启思考纠错，`disabled` 直接输出 |
| `SILICONFLOW_API_KEY` | — | 硅基流动 API Key（使用 cloud 模式时必填） |
| `WHISPER_MODEL` | `FunAudioLLM/SenseVoiceSmall` | 云端 ASR 模型 |
| `ASR_BACKEND` | `local` | `local` 本地 faster-whisper，`cloud` 硅基流动 |
| `WHISPER_MODEL_SIZE` | `medium` | 本地模型大小：tiny/base/small/medium/large-v3 |

### 切换 ASR 后端

```bash
# 本地模式（默认）
set ASR_BACKEND=local
set WHISPER_MODEL_SIZE=medium

# 云端模式（硅基流动）
set ASR_BACKEND=cloud
set SILICONFLOW_API_KEY=sk-your-key
```

### 切换翻译模型

```bash
set LLM_MODEL=kimi-k2.6
set THINKING_MODE=enabled   # 启用思考模式，自动纠错能力更强
```

---

## 工作流程详解

```
raw/sample.mp4
    │
    ▼
step1_extract_audio.py
    │  ffmpeg 提取 16kHz 单声道音频
    ▼
temp/sample/audio.wav
    │
    ▼
step2_transcribe.py
    │  faster-whisper 转写 → 带时间轴的 SRT
    ▼
output/sample/sample_src.srt
    │
    ▼
step3_translate.py
    │  1. 从 SRT 提取纯文本（每行一句）
    │  2. 流式上传给 Kimi，逐行翻译
    │  3. 译文映射回原时间轴 → 新 SRT
    │  4. 保存 LLM 原始输出到 temp/sample/sample_llm_raw.md
    ▼
output/sample/sample_zh.srt
    │
    ▼
step4_burn_subtitles.py
    │  ffmpeg 将字幕硬编码到视频画面
    ▼
output/sample/sample_zh.mp4
```

### 为什么只传纯文本给 LLM？

传统做法是把整个 SRT（含序号、时间轴 `00:00:01,000 --> 00:00:03,000`）上传给 LLM，要求它"保持格式"。但：
- 时间轴占大量 token，浪费 API 费用
- LLM 容易破坏 SRT 格式，导致时间轴错位
- 无关信息干扰翻译质量

本工作流的做法：
1. 本地解析 SRT，只提取 `content`（纯文本）
2. 用换行符连接，上传给 LLM
3. LLM 只负责翻译文本，无需关心格式
4. 本地将译文按顺序映射回原时间轴

这样时间轴 100% 准确，token 消耗降低 30%~50%。

---

## 二次开发指南

### 替换 ASR 引擎

如果你想用其他语音识别服务（如 OpenAI 官方 Whisper、阿里云、讯飞等），修改 `step2_transcribe.py`：

```python
# 在 transcribe_local() 或新增 transcribe_xxx() 函数中
# 调用你的 ASR API，最终写入 srt_path
```

关键约束：输出必须是**标准 SRT 格式**（含时间轴），因为 `step3_translate.py` 会解析它提取纯文本。

### 替换翻译模型

修改 `step3_translate.py` 顶部的配置：

```python
LLM_API_KEY = os.getenv("YOUR_API_KEY", "")
LLM_BASE_URL = "https://api.yourservice.com/v1"
LLM_MODEL = os.getenv("LLM_MODEL", "your-model-name")
```

如果新模型**不支持 `thinking` 参数**（如 GPT-4o），删除 `extra_body` 相关代码即可：

```python
# 删除这段
extra_body = {}
if THINKING_MODE == "disabled":
    extra_body["thinking"] = {"type": "disabled"}
...
stream = client.chat.completions.create(
    ...,
    extra_body=extra_body,  # 删除这行
    stream=True,
)
```

### 修改前端界面

`app.py` 使用 Gradio Blocks 构建。常见扩展：

**添加新的配置项**：
```python
# 在左侧面板添加下拉框
my_config = gr.Dropdown(choices=["a", "b"], value="a", label="我的配置")

# 在 run_step 的 inputs 中加入它
s2_btn.click(run_step, inputs=[..., my_config], outputs=log_box)
```

**添加新步骤按钮**：
```python
s5_btn = gr.Button("5️⃣ 我的步骤", size="sm")
s5_btn.click(
    run_step,
    inputs=[gr.State("step5_my_step.py"), video_select, ...],
    outputs=log_box,
).success(
    refresh_output_info, inputs=video_select, outputs=output_info
)
```

**修改 CSS 样式**：
```python
CSS = """
.fixed-log textarea { height: 400px !important; }
/* 你的新样式 */
"""
```

### 添加新步骤

创建 `step5_xxx.py`，遵循以下约定：

1. **输入**：接受视频路径作为 `sys.argv[1]`
2. **输出**：写入 `temp/{stem}/` 或 `output/{stem}/`
3. **错误处理**：返回非零退出码时，前端会停止后续步骤

模板：

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

RAW_DIR = Path("raw")
OUTPUT_DIR = Path("output")

def main():
    video_path = Path(sys.argv[1])
    stem = video_path.stem
    work_output = OUTPUT_DIR / stem
    work_output.mkdir(parents=True, exist_ok=True)
    
    # 读取前一步的输出
    input_file = work_output / f"{stem}_zh.srt"
    # ... 你的处理逻辑 ...
    
    # 写入输出
    output_file = work_output / f"{stem}_new.ext"
    output_file.write_text("...", encoding="utf-8")
    print(f"[完成] -> {output_file}")

if __name__ == "__main__":
    main()
```

然后在 `app.py` 中注册按钮和 `.success()` 链。

### 修改字幕编辑器的显示格式

当前字幕编辑器直接显示 SRT 纯文本。如果你想显示更友好的格式（如表格），修改 `load_subtitles()`：

```python
def load_subtitles(video_path: str):
    import srt
    subs = list(srt.parse(src_path.read_text(encoding="utf-8")))
    lines = [f"{i+1}. [{sub.start}] {sub.content}" for i, sub in enumerate(subs)]
    return "\n".join(lines), ...
```

> 注意：保存时需要把友好格式转回标准 SRT，否则 `step4` 无法读取。

---

## 常见问题

### Q1: Windows 终端输出乱码？

A: `app.py` 已内置 `PYTHONIOENCODING=utf-8`，确保子进程用 UTF-8 输出。如仍乱码，检查系统区域设置是否开启"Beta: Use Unicode UTF-8"。

### Q2: faster-whisper 模型下载很慢？

A: 设置 HuggingFace 国内镜像：
```bash
set HF_ENDPOINT=https://hf-mirror.com
python download_model.py medium
```

### Q3: 4GB 显存跑 large-v3 报错 OOM？

A: `large-v3` FP16 需要 ~10GB 显存。4GB 卡请使用 `medium` + INT8（默认配置）。

### Q4: 翻译后的字幕时间轴错位？

A: 本工作流采用"纯文本翻译 + 本地重组时间轴"策略，时间轴完全由原始 SRT 继承，理论上不会错位。如发现错位，请检查 `step2` 生成的 `_src.srt` 是否本身有时间轴问题。

### Q5: 如何只生成字幕文件，不烧录视频？

A: 执行到 `step3` 即可，`output/{stem}/{stem}_zh.srt` 就是最终译文字幕。跳过 `step4` 不执行烧录。

### Q6: 思考模式和非思考模式有什么区别？

A: 
- `enabled`：K2.6 先内部思考再输出，擅长纠错（如修正 Whisper 听错的人名/术语），但输出更慢
- `disabled`：直接翻译，速度快，适合校对后批量处理

---

## License

MIT
