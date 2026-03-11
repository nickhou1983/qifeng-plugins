#!/usr/bin/env python3
"""
Azure OpenAI Sora-2 文本生成视频脚本 (Text-to-Video)
根据文本描述直接生成视频
"""

import argparse
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


def load_config() -> dict:
    """加载 .env 配置文件"""
    skill_dir = Path(__file__).parent
    env_path = skill_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    config = {
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "deployment": os.getenv("AZURE_OPENAI_SORA_DEPLOYMENT", "sora"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "preview"),
        "video_api_mode": os.getenv("AZURE_OPENAI_VIDEO_API_MODE", "jobs").lower(),
    }

    if not config["endpoint"] or not config["api_key"]:
        print("错误: 请配置 AZURE_OPENAI_ENDPOINT 和 AZURE_OPENAI_API_KEY")
        print(f"可以在 {skill_dir / '.env'} 文件中设置，参考 .env.example")
        sys.exit(1)

    if config["video_api_mode"] not in ("auto", "legacy", "jobs"):
        print("错误: AZURE_OPENAI_VIDEO_API_MODE 仅支持 auto / legacy / jobs")
        sys.exit(1)

    return config


def get_video_submit_url(config: dict, mode: str) -> str:
    """构建视频生成提交 URL"""
    if mode == "jobs":
        return (
            f"{config['endpoint'].rstrip('/')}/openai/v1/video/generations/jobs"
            f"?api-version={config['api_version']}"
        )
    return (
        f"{config['endpoint'].rstrip('/')}/openai/deployments/{config['deployment']}"
        f"/videos/generations?api-version={config['api_version']}"
    )


def get_video_status_url(config: dict, mode: str, job_id: str) -> str:
    """构建视频生成状态查询 URL"""
    if mode == "jobs":
        return (
            f"{config['endpoint'].rstrip('/')}/openai/v1/video/generations/jobs/{job_id}"
            f"?api-version={config['api_version']}"
        )
    return (
        f"{config['endpoint'].rstrip('/')}/openai/deployments/{config['deployment']}"
        f"/videos/generations/{job_id}?api-version={config['api_version']}"
    )


def get_video_content_url(config: dict, route_mode: str, generation_id: str) -> str:
    """构建视频内容下载 URL"""
    if route_mode == "jobs":
        return (
            f"{config['endpoint'].rstrip('/')}/openai/v1/video/generations/{generation_id}"
            f"/content/video?api-version={config['api_version']}"
        )
    return ""


def resolve_probe_modes(config: dict) -> list[str]:
    """根据配置解析需要探测的路由模式"""
    if config["video_api_mode"] == "auto":
        return ["jobs", "legacy"]
    return [config["video_api_mode"]]


def parse_video_size(size: str) -> tuple[int, int]:
    """解析视频尺寸字符串"""
    try:
        width_str, height_str = size.lower().split("x")
        width, height = int(width_str), int(height_str)
    except ValueError:
        raise ValueError("size 格式必须为 宽x高，例如 1920x1080")
    if width <= 0 or height <= 0:
        raise ValueError("size 的宽和高必须为正整数")
    return width, height


def preflight_video_generation_route(config: dict) -> str:
    """提交正式任务前，先探测视频路由是否可用"""
    headers = {
        "api-key": config["api_key"],
        "Content-Type": "application/json",
    }

    not_found_urls = []
    for mode in resolve_probe_modes(config):
        url = get_video_submit_url(config, mode)
        try:
            response = requests.post(url, headers=headers, json={}, timeout=20)
        except requests.RequestException as exc:
            print(f"错误: 无法连接到 Azure OpenAI 端点 - {exc}")
            sys.exit(1)

        if response.status_code == 404:
            not_found_urls.append(url)
            continue

        if response.status_code in (401, 403):
            print(f"错误: 预检查失败 (HTTP {response.status_code})，请检查 API Key 或访问权限")
            sys.exit(1)

        return mode

    print("错误: 当前资源未暴露可用的 Sora 视频生成路由（HTTP 404）")
    print("请检查以下配置：")
    print(f"  endpoint: {config['endpoint']}")
    print(f"  deployment: {config['deployment']}")
    print(f"  api-version: {config['api_version']}")
    if not_found_urls:
        print("已探测路由:")
        for url in not_found_urls:
            print(f"  - {url}")
    sys.exit(1)


def submit_text_to_video(
    config: dict,
    route_mode: str,
    prompt: str,
    size: str,
    n_seconds: int,
) -> str:
    """提交文生视频任务，返回任务 ID"""
    url = get_video_submit_url(config, route_mode)
    headers = {
        "api-key": config["api_key"],
        "Content-Type": "application/json",
    }

    if route_mode == "jobs":
        try:
            width, height = parse_video_size(size)
        except ValueError as exc:
            print(f"错误: {exc}")
            sys.exit(1)

        payload = {
            "prompt": prompt,
            "n_variants": "1",
            "n_seconds": str(n_seconds),
            "height": str(height),
            "width": str(width),
            "model": config["deployment"],
        }
    else:
        payload = {
            "prompt": prompt,
            "size": size,
            "n_seconds": n_seconds,
        }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code not in (200, 201, 202):
        print(f"错误: 提交文生视频任务失败 (HTTP {response.status_code})")
        print(f"响应: {response.text}")
        sys.exit(1)

    data = response.json()
    job_id = data.get("id") or data.get("job_id") or data.get("jobId")
    if not job_id:
        print(f"错误: 未能从响应中获取任务 ID - {data}")
        sys.exit(1)

    return job_id


def poll_video_status(
    config: dict, route_mode: str, job_id: str, poll_interval: int = 10, max_wait: int = 600
) -> dict:
    """轮询视频生成任务状态"""
    url = get_video_status_url(config, route_mode, job_id)
    headers = {"api-key": config["api_key"]}

    elapsed = 0
    while elapsed < max_wait:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"  警告: 查询状态失败 (HTTP {response.status_code})，将重试...")
            time.sleep(poll_interval)
            elapsed += poll_interval
            continue

        data = response.json()
        status = data.get("status", "unknown")

        if status == "succeeded":
            print("✅ 视频生成完成！")
            return data
        elif status == "failed":
            error_msg = data.get("error", {}).get("message", "未知错误")
            print(f"错误: 视频生成失败 - {error_msg}")
            sys.exit(1)
        else:
            print(f"  状态: {status}，已等待 {elapsed}s...")
            time.sleep(poll_interval)
            elapsed += poll_interval

    print(f"错误: 视频生成超时（已等待 {max_wait} 秒）")
    sys.exit(1)


def download_video(video_url: str, output_path: str, headers: dict | None = None) -> str:
    """下载视频文件并保存到本地"""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print("正在下载视频...")
    response = requests.get(video_url, headers=headers, stream=True, timeout=120)
    if response.status_code != 200:
        print(f"错误: 下载视频失败 (HTTP {response.status_code})")
        sys.exit(1)

    with open(output_file, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"🎬 视频已保存到: {output_file.resolve()}")
    return str(output_file.resolve())


def generate_video(
    prompt: str,
    output_path: str = "./output.mp4",
    size: str = "1920x1080",
    n_seconds: int = 5,
    poll_interval: int = 10,
    max_wait: int = 600,
) -> str:
    """
    调用 Azure OpenAI Sora-2 文生视频

    Args:
        prompt: 视频描述文本
        output_path: 输出视频文件路径
        size: 视频尺寸 (宽x高)
        n_seconds: 视频时长（秒）
        poll_interval: 轮询间隔（秒）
        max_wait: 最大等待时间（秒）

    Returns:
        保存的视频文件路径
    """
    config = load_config()

    print("🎬 Azure OpenAI Sora-2 文生视频")
    print(f"  描述: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"  尺寸: {size}")
    print(f"  时长: {n_seconds} 秒")
    print(f"  模型: {config['deployment']}")

    # 预检查路由
    print("正在检查 API 路由...")
    route_mode = preflight_video_generation_route(config)
    print(f"  路由模式: {route_mode}")

    # 提交生成任务
    print("正在提交文生视频任务...")
    job_id = submit_text_to_video(config, route_mode, prompt, size, n_seconds)
    print(f"  任务 ID: {job_id}")

    # 轮询等待完成
    print(f"等待视频生成（轮询间隔: {poll_interval}s，超时: {max_wait}s）...")
    result = poll_video_status(config, route_mode, job_id, poll_interval, max_wait)

    # 提取视频 URL 并下载
    video_url = result.get("video_url") or result.get("videoUrl")
    if not video_url:
        output = result.get("output", {})
        if isinstance(output, dict):
            video_url = output.get("video_url") or output.get("videoUrl")

    generations = result.get("generations", [])
    if not video_url and generations:
        video_url = generations[0].get("video", {}).get("url")

    # jobs 模式：通过 content API 下载
    if not video_url and route_mode == "jobs" and generations:
        generation_id = generations[0].get("id")
        if generation_id:
            content_url = get_video_content_url(config, route_mode, generation_id)
            return download_video(content_url, output_path, headers={"api-key": config["api_key"]})

    if not video_url:
        print(f"错误: 未能从响应中获取视频 URL - {result}")
        sys.exit(1)

    return download_video(video_url, output_path)


def main():
    parser = argparse.ArgumentParser(
        description="使用 Azure OpenAI Sora-2 根据文本描述生成视频（Text-to-Video）"
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="视频描述文本",
    )
    parser.add_argument(
        "--output",
        default="./output.mp4",
        help="输出视频文件路径（默认: ./output.mp4）",
    )
    parser.add_argument(
        "--size",
        default="1920x1080",
        help="视频尺寸，格式 宽x高（默认: 1920x1080）",
    )
    parser.add_argument(
        "--n-seconds",
        type=int,
        default=5,
        choices=[5, 10, 15, 20],
        help="视频时长/秒（默认: 5）",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="轮询间隔/秒（默认: 10）",
    )
    parser.add_argument(
        "--max-wait",
        type=int,
        default=600,
        help="最大等待时间/秒（默认: 600）",
    )

    args = parser.parse_args()

    generate_video(
        prompt=args.prompt,
        output_path=args.output,
        size=args.size,
        n_seconds=args.n_seconds,
        poll_interval=args.poll_interval,
        max_wait=args.max_wait,
    )


if __name__ == "__main__":
    main()
