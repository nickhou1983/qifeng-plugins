#!/usr/bin/env python3
"""
共享 GitHub API 客户端
提供统一的配置加载、请求头构建和错误处理
"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# GitHub API 默认版本（Copilot 端点需要此预览版本）
DEFAULT_API_VERSION = "2022-11-28"

# 错误信息映射
ERROR_MESSAGES = {
    401: "认证失败：请检查 GITHUB_TOKEN 是否有效。",
    403: "权限不足：请确认 PAT 具有所需权限。\n"
         "  - Organization 模式需要 manage_billing:copilot 或 read:org\n"
         "  - Enterprise 模式需要 PAT (classic) + manage_billing:copilot 或 read:enterprise\n"
         "  注意：Enterprise 端点不支持 Fine-grained PAT。",
    404: "资源未找到：请检查组织名/企业名是否正确，以及该组织/企业是否启用了 Copilot。",
    422: "请求参数无效：请检查传入的参数格式。",
}


def load_env():
    """加载 .env 配置文件，优先从脚本所在 skill 目录加载，其次从插件根目录加载"""
    # 脚本所在目录的上两级为 skill 目录
    script_dir = Path(__file__).resolve().parent
    skill_dir = script_dir.parent
    plugin_root = skill_dir.parent.parent

    for candidate in [skill_dir / ".env", plugin_root / ".env"]:
        if candidate.exists():
            load_dotenv(candidate)
            return

    # 没有找到 .env 文件也不报错，允许环境变量直接设置
    load_dotenv()


def get_config() -> dict:
    """获取 GitHub API 配置"""
    load_env()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("错误: 请设置 GITHUB_TOKEN 环境变量或在 .env 文件中配置。")
        print("参考 .env.example 文件了解所需配置。")
        sys.exit(1)

    return {
        "token": token,
        "api_version": os.getenv("GITHUB_API_VERSION", DEFAULT_API_VERSION),
        "org": os.getenv("GITHUB_ORG", ""),
        "enterprise": os.getenv("GITHUB_ENTERPRISE", ""),
    }


def get_headers(config: dict) -> dict:
    """构建 GitHub API 请求头"""
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {config['token']}",
        "X-GitHub-Api-Version": config["api_version"],
    }


def api_request(method: str, url: str, config: dict, params: dict = None) -> dict:
    """
    发送 GitHub API 请求并处理通用错误

    Returns:
        响应 JSON 数据
    """
    headers = get_headers(config)

    try:
        response = requests.request(
            method, url, headers=headers, params=params, timeout=30
        )
    except requests.RequestException as exc:
        print(f"错误: 无法连接到 GitHub API - {exc}")
        sys.exit(1)

    if response.status_code == 200:
        return response.json()

    error_msg = ERROR_MESSAGES.get(
        response.status_code,
        f"API 请求失败 (HTTP {response.status_code})",
    )
    print(f"错误: {error_msg}")
    print(f"URL: {url}")

    try:
        detail = response.json()
        if "message" in detail:
            print(f"详情: {detail['message']}")
    except Exception:
        if response.text:
            print(f"响应: {response.text[:500]}")

    sys.exit(1)


def api_request_paginated(url: str, config: dict, params: dict = None, per_page: int = 100) -> list:
    """
    发送分页 GitHub API 请求，自动遍历所有页面

    Returns:
        所有页面合并后的数据列表
    """
    if params is None:
        params = {}
    params["per_page"] = per_page
    params["page"] = 1

    all_items = []
    while True:
        data = api_request("GET", url, config, params=params)

        # 不同端点返回结构不同，有些直接返回列表，有些返回对象
        if isinstance(data, list):
            all_items.extend(data)
            if len(data) < per_page:
                break
        elif isinstance(data, dict):
            # 例如 seats 端点返回 {total_seats: N, seats: [...]}
            items = data.get("seats", data.get("items", []))
            all_items.extend(items)
            if len(items) < per_page:
                break
        else:
            break

        params["page"] += 1

    return all_items


def resolve_scope(args) -> tuple:
    """
    根据命令行参数解析查询范围

    Returns:
        (scope, name) — scope 为 "org" 或 "enterprise"，name 为组织名或企业名
    """
    config = get_config()

    scope = getattr(args, "scope", "org")
    if scope == "org":
        name = getattr(args, "org", None) or config["org"]
        if not name:
            print("错误: 请通过 --org 参数或 GITHUB_ORG 环境变量指定组织名称。")
            sys.exit(1)
    else:
        name = getattr(args, "enterprise", None) or config["enterprise"]
        if not name:
            print("错误: 请通过 --enterprise 参数或 GITHUB_ENTERPRISE 环境变量指定企业名称。")
            sys.exit(1)

    return scope, name, config
