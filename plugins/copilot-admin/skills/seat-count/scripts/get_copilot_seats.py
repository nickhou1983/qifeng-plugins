#!/usr/bin/env python3
"""
GitHub Copilot 许可数量查询脚本
支持组织级和企业级查询，输出 seat 统计摘要和 Top N 非活跃用户明细
"""

import argparse
import sys
from pathlib import Path

# 将 common 目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "common"))

from github_client import api_request, api_request_paginated, get_config, resolve_scope


def get_org_seat_summary(config: dict, org: str) -> dict:
    """获取组织级 Copilot 许可统计摘要"""
    url = f"https://api.github.com/orgs/{org}/copilot/billing"
    data = api_request("GET", url, config)

    breakdown = data.get("seat_breakdown", {})
    return {
        "total": breakdown.get("total", 0),
        "active_this_cycle": breakdown.get("active_this_cycle", 0),
        "inactive_this_cycle": breakdown.get("inactive_this_cycle", 0),
        "pending_invitation": breakdown.get("pending_invitation", 0),
        "pending_cancellation": breakdown.get("pending_cancellation", 0),
        "added_this_cycle": breakdown.get("added_this_cycle", 0),
    }


def get_org_seats_detail(config: dict, org: str) -> list:
    """获取组织级所有 seat 明细（分页）"""
    url = f"https://api.github.com/orgs/{org}/copilot/billing/seats"
    return api_request_paginated(url, config)


def get_enterprise_seats(config: dict, enterprise: str) -> tuple:
    """
    获取企业级 Copilot seat 数据
    企业端点没有 seat_breakdown 摘要，需从 seats 列表自行统计

    Returns:
        (total_seats, seats_list)
    """
    url = f"https://api.github.com/enterprises/{enterprise}/copilot/billing/seats"

    # 先取第一页获取 total_seats
    first_page = api_request("GET", url, config, params={"per_page": 100, "page": 1})
    total_seats = first_page.get("total_seats", 0)

    # 收集所有 seat 明细
    seats = first_page.get("seats", [])
    page = 2
    while len(first_page.get("seats", [])) == 100:
        next_page = api_request("GET", url, config, params={"per_page": 100, "page": page})
        page_seats = next_page.get("seats", [])
        seats.extend(page_seats)
        if len(page_seats) < 100:
            break
        first_page = next_page
        page += 1

    return total_seats, seats


def compute_enterprise_summary(total_seats: int, seats: list) -> dict:
    """从企业 seats 列表统计摘要信息"""
    pending_cancellation = sum(
        1 for s in seats if s.get("pending_cancellation_date") is not None
    )
    active = sum(
        1 for s in seats if s.get("last_activity_at") is not None
    )
    inactive = len(seats) - active

    return {
        "total_seats": total_seats,
        "active": active,
        "inactive": inactive,
        "pending_cancellation": pending_cancellation,
    }


def get_top_inactive_seats(seats: list, top_n: int) -> list:
    """
    获取 Top N 非活跃 seat（按 last_activity_at 升序排列）
    last_activity_at 为 None 的排在最前面（从未使用过）
    """
    if top_n <= 0:
        return []

    sorted_seats = sorted(
        seats,
        key=lambda s: (
            s.get("last_activity_at") is not None,  # None 排前面
            s.get("last_activity_at") or "",
        ),
    )
    return sorted_seats[:top_n]


def print_org_report(summary: dict, inactive_seats: list):
    """输出组织级报告"""
    print("=" * 60)
    print("GitHub Copilot 许可统计报告（Organization）")
    print("=" * 60)
    print(f"  已分配 seat 总数:       {summary['total']}")
    print(f"  本周期活跃:             {summary['active_this_cycle']}")
    print(f"  本周期不活跃:           {summary['inactive_this_cycle']}")
    print(f"  待接受邀请:             {summary['pending_invitation']}")
    print(f"  待取消:                 {summary['pending_cancellation']}")
    print(f"  本周期新增:             {summary['added_this_cycle']}")

    if inactive_seats:
        print()
        print(f"Top {len(inactive_seats)} 非活跃 Seat 明细:")
        print("-" * 60)
        print(f"  {'用户':<30} {'最后活跃时间':<25}")
        print("-" * 60)
        for seat in inactive_seats:
            assignee = seat.get("assignee", {})
            login = assignee.get("login", "N/A") if assignee else "N/A"
            last_activity = seat.get("last_activity_at") or "从未使用"
            print(f"  {login:<30} {last_activity:<25}")

    print()


def print_enterprise_report(summary: dict, inactive_seats: list):
    """输出企业级报告"""
    print("=" * 60)
    print("GitHub Copilot 许可统计报告（Enterprise）")
    print("=" * 60)
    print(f"  已分配 seat 总数:       {summary['total_seats']}")
    print(f"  有活动记录:             {summary['active']}")
    print(f"  无活动记录:             {summary['inactive']}")
    print(f"  待取消:                 {summary['pending_cancellation']}")

    if inactive_seats:
        print()
        print(f"Top {len(inactive_seats)} 非活跃 Seat 明细:")
        print("-" * 60)
        print(f"  {'用户':<30} {'最后活跃时间':<25}")
        print("-" * 60)
        for seat in inactive_seats:
            assignee = seat.get("assignee", {})
            login = assignee.get("login", "N/A") if assignee else "N/A"
            last_activity = seat.get("last_activity_at") or "从未使用"
            print(f"  {login:<30} {last_activity:<25}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="查询 GitHub Copilot 许可数量及使用状态"
    )
    parser.add_argument(
        "--scope",
        choices=["org", "enterprise"],
        default="org",
        help="查询范围：org（组织级）或 enterprise（企业级），默认 org",
    )
    parser.add_argument("--org", help="组织名称（scope=org 时使用，也可通过 GITHUB_ORG 环境变量设置）")
    parser.add_argument("--enterprise", help="企业 slug（scope=enterprise 时使用，也可通过 GITHUB_ENTERPRISE 环境变量设置）")
    parser.add_argument(
        "--top-inactive",
        type=int,
        default=10,
        help="显示 Top N 非活跃 seat 明细，设为 0 跳过（默认 10）",
    )

    args = parser.parse_args()
    scope, name, config = resolve_scope(args)

    if scope == "org":
        print(f"正在查询组织 [{name}] 的 Copilot 许可数据...")
        summary = get_org_seat_summary(config, name)

        inactive_seats = []
        if args.top_inactive > 0:
            seats = get_org_seats_detail(config, name)
            inactive_seats = get_top_inactive_seats(seats, args.top_inactive)

        print_org_report(summary, inactive_seats)
    else:
        print(f"正在查询企业 [{name}] 的 Copilot 许可数据...")
        total_seats, seats = get_enterprise_seats(config, name)
        summary = compute_enterprise_summary(total_seats, seats)

        inactive_seats = []
        if args.top_inactive > 0:
            inactive_seats = get_top_inactive_seats(seats, args.top_inactive)

        print_enterprise_report(summary, inactive_seats)


if __name__ == "__main__":
    main()
