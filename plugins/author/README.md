# Author Plugin

Generate cinematic video descriptions and storyboards, and call Azure OpenAI Sora-2 to produce videos.

## Skills

| Skill | Description |
|-------|-------------|
| **author** | 生成电影感视频描述和分镜脚本，将创意转化为视觉叙事，适配 Sora、Runway、Kling 等文生视频模型 |
| **video-gen** | 调用 Azure OpenAI Sora-2 API 生成视频，支持单镜头和分镜批量生成 |

## Workflow

1. **创意输入** — 用户描述想要的视频主题、风格、时长
2. **描述生成** — `author` skill 生成电影感的视频描述或分镜脚本
3. **视频生成** — `video-gen` skill 调用 Azure OpenAI Sora-2 生成实际视频
4. **多镜头拼接** — 分镜模式下可通过 ffmpeg 拼接多个镜头

## Prerequisites

- Azure OpenAI 资源，已部署 `sora` 模型
- Python 3.10+
- 配置 `.env` 文件（参考 `skills/video-gen/.env.example`）

## Installation

```bash
cd plugins/author/skills/video-gen
cp .env.example .env
# 编辑 .env 填入你的 Azure OpenAI 配置
pip install -r requirements.txt
```

## License

MIT
