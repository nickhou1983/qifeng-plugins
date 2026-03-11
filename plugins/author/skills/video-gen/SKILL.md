---
name: video-gen
description: "调用 Azure OpenAI Sora-2 生成视频。Use when: 用户要求生成视频、文生视频、text-to-video、调用 Sora 生成视频、批量生成镜头并拼接。支持单镜头和分镜批量生成。"
---

# Video Gen — Azure OpenAI Sora-2 视频生成

调用 Azure OpenAI Sora-2 API，根据文本 prompt 生成视频文件。支持单镜头生成和分镜脚本批量生成 + 拼接。

## 触发场景

- 用户提供一段视频描述，要求生成视频
- 用户有一组分镜脚本，要求逐镜头生成并拼接
- 用户要求调用 Sora / Azure OpenAI 生成视频

## 前置要求

1. 已部署 Azure OpenAI `sora` 模型
2. 在 Skill 目录下配置 `.env` 文件（参考 [.env.example](./.env.example)）
3. 已安装 Python 3.10+、`requests` 和 `python-dotenv`

安装依赖：

```bash
pip install -r ./requirements.txt
```

## 环境配置

复制 `.env.example` 为 `.env` 并填入实际配置：

```text
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_SORA_DEPLOYMENT=sora
AZURE_OPENAI_API_VERSION=preview
AZURE_OPENAI_VIDEO_API_MODE=jobs
```

确保 `.env` 不被提交到版本控制。

## 工作流程

### Step 1: 确认 prompt

如果用户直接提供了视频描述文本，直接使用。如果描述是中文，建议同时准备英文版本（英文 prompt 生成效果更佳）。

如果用户还没有描述，建议使用 `author` 技能先生成电影感视频描述。

### Step 2: 单镜头生成

使用 [generate_video.py](./scripts/generate_video.py) 生成视频：

```bash
python ./scripts/generate_video.py \
  --prompt "<视频描述文本>" \
  --output "./output/video.mp4" \
  --size "1920x1080" \
  --n-seconds 10
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--prompt` | 是 | - | 视频描述文本（英文效果最佳） |
| `--output` | 否 | `./output.mp4` | 输出视频文件路径 |
| `--size` | 否 | `1920x1080` | 视频尺寸（宽x高） |
| `--n-seconds` | 否 | `5` | 视频时长（5/10/15/20 秒） |
| `--poll-interval` | 否 | `10` | 轮询间隔（秒） |
| `--max-wait` | 否 | `600` | 最大等待时间（秒） |

### Step 3: 分镜批量生成

当有多个镜头需要生成时，逐镜头调用并拼接：

```bash
# 镜头 1
python ./scripts/generate_video.py \
  --prompt "<镜头1 描述>" \
  --output "./output/shot_01.mp4" \
  --n-seconds 6

# 镜头 2
python ./scripts/generate_video.py \
  --prompt "<镜头2 描述>" \
  --output "./output/shot_02.mp4" \
  --n-seconds 6

# 依此类推...
```

### Step 4: 拼接镜头

使用 `ffmpeg` 将所有镜头拼接为完整视频（需要已安装 ffmpeg）：

```bash
# 创建文件列表
ls ./output/shot_*.mp4 | sort | sed "s/^/file '/" | sed "s/$/'/" > ./output/filelist.txt

# 拼接
ffmpeg -f concat -safe 0 -i ./output/filelist.txt -c copy ./output/final.mp4
```

如果 `ffmpeg` 未安装：`brew install ffmpeg`（macOS）

## 注意事项

- 视频生成是异步过程，每个镜头可能需要等待数分钟
- 推荐使用英文 prompt 以获得最佳生成效果
- 如果 API 配置未设置，脚本会给出明确的配置提示
- 支持 `jobs` 和 `legacy` 两种 Azure API 路由模式，默认使用 `jobs`
