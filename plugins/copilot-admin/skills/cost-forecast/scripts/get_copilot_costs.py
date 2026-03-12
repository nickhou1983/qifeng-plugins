#!/usr/bin/env python3
"""
GitHub Copilot 费用与月底预估查询脚本
支持组织级和企业级查询，输出当前累计费用、日均费用和月底预估费用
"""

import argparse
import sys
from calendar import monthrange
from datetime import date, datetime, timezone
from pathlib import Path

# 将 common 目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "common"))

from github_client import api_request, get_config, resolve_scope


def get_billing_usage_summary(config: dict, scope: str, name: str) -> dict:
    """获取 Billing Usage Summary"""
    if scope == "org":
        url = f"https://api.github.com/organizations/{name}/settings/billing/usage/summary"
    else:
        url = f"https://api.github.com/enterprises/{name}/settings/billing/usage/summary"
    return api_request("GET", url, config)


def get_premium_request_usage(config: dict, scope: str, name: str) -> dict:
    """获取 Premium Request Usage"""
    if scope == "org":
        url = f"https://api.github.com/organizations/{name}/settings/billing/premium_request/usage"
    else:
        url = f"https://api.github.com/enterprises/{name}/settings/billing/premium_request/usage"
    return api_request("GET", url, config)


def filter_usage_items(data: dict, product_filter: str) -> list:
    """
    按 product 名称过滤 usageItems
    大小写不敏感的包含匹配
    """
    usage_items = data.get("usageItems", [])
    if not product_filter:
        return usage_items

    product_lower = product_filter.lower()
    return [
        item for item in usage_items
        if product_lower in (item.get("product", "") or "").lower()
        or product_lower in (item.get("sku", "") or "").lower()
    ]


def compute_cost_summary(usage_items: list, premium_items: list) -> dict:
    """
    计算费用汇总

    Returns:
        {
            "base_net_amount": float,   基础订阅费用
            "premium_net_amount": float, Premium Requests 费用
            "total_net_amount": float,  总计
            "premium_details": list,    Premium Requests 明细
        }
    """
    base_net = sum(float(item.get("netAmount", 0)) for item in usage_items)

    premium_net = sum(float(item.get("netAmount", 0)) for item in premium_items)
    premium_details = []
    for item in premium_items:
        premium_details.append({
            "sku": item.get("sku", "N/A"),
            "quantity": item.get("quantity", 0),
            "unit_price": item.get("pricePerUnit", 0),
            "net_amount": float(item.get("netAmount", 0)),
            "gross_amount": float(item.get("grossAmount", 0)),
        })

    return {
        "base_net_amount": base_net,
        "premium_net_amount": premium_net,
        "total_net_amount": base_net + premium_net,
        "premium_details": premium_details,
    }


def compute_forecast(total_net_amount: float) -> dict:
    """
    计算月底预估费用

    公式：月底预估费用 = 当前累计费用 / 已过天数 × 当月总天数
    """
    today = date.today()
    days_in_month = monthrange(today.year, today.month)[1]

    # 使用当前时间计算更精确的已过天数（含小数）
    now = datetime.now(timezone.utc)
    start_of_month = datetime(today.year, today.month, 1, tzinfo=timezone.utc)
    elapsed_days = (now - start_of_month).total_seconds() / 86400

    if elapsed_days < 0.5:
        # 月初不到半天数据，不做预估
        return {
            "days_elapsed": round(elapsed_days, 1),
            "days_in_month": days_in_month,
            "daily_average": 0,
            "forecast": 0,
            "note": "月初数据不足半天，暂不做预估",
        }

    daily_average = total_net_amount / elapsed_days
    forecast = daily_average * days_in_month

    return {
        "days_elapsed": round(elapsed_days, 1),
        "days_in_month": days_in_month,
        "daily_average": round(daily_average, 2),
        "forecast": round(forecast, 2),
        "note": "",
    }


def print_report(scope: str, name: str, product_filter: str, cost: dict, forecast: dict):
    """输出费用报告"""
    scope_label = "Organization" if scope == "org" else "Enterprise"

    print("=" * 60)
    print(f"GitHub Copilot 费用报告（{scope_label}）")
    print("=" * 60)
    print(f"  查询目标:               {name}")
    print(f"  产品过滤:               {product_filter}")
    print(f"  查询日期:               {date.today().isoformat()}")
    print()
    print("费用汇总:")
    print(f"  基础订阅费用:           ${cost['base_net_amount']:.2f}")
    print(f"  Premium Requests 费用:  ${cost['premium_net_amount']:.2f}")
    print(f"  当月累计费用:           ${cost['total_net_amount']:.2f}")
    print()
    print("月底预估:")
    print(f"  本月已过天数:           {forecast['days_elapsed']} / {forecast['days_in_month']} 天")

    if forecast["note"]:
        print(f"  ⚠️  {forecast['note']}")
    else:
        print(f"  日均费用:               ${forecast['daily_average']:.2f}")
        print(f"  月底预估费用:           ${forecast['forecast']:.2f}")

    if cost["premium_details"]:
        print()
        print("Premium Requests 明细:")
        print("-" * 60)
        print(f"  {'SKU':<35} {'数量':>8} {'金额':>10}")
        print("-" * 60)
        for detail in cost["premium_details"]:
            print(f"  {detail['sku']:<35} {detail['quantity']:>8} ${detail['net_amount']:>9.2f}")

    print()
    print("口径说明:")
    print("  - 当月累计费用 = Billing Usage Summary 中匹配产品的 netAmount 总和")
    print("    + Premium Request Usage 中匹配产品的 netAmount 总和")
    print("  - 月底预估费用 = 当月累计费用 / 已过天数 × 当月总天数（线性外推）")
    print("  - 预估值假设后续日均用量与当前一致，仅供参考")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="查询 GitHub Copilot 当前费用和预估月底费用"
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
        "--product",
        default="Copilot",
        help="按产品名称过滤（大小写不敏感包含匹配），默认 Copilot",
    )

    args = parser.parse_args()
    scope, name, config = resolve_scope(args)

    scope_label = "组织" if scope == "org" else "企业"
    print(f"正在查询{scope_label} [{name}] 的 Copilot 费用数据...")

    # 获取基础用量汇总
    usage_data = get_billing_usage_summary(config, scope, name)
    usage_items = filter_usage_items(usage_data, args.product)

    # 获取 Premium Request 用量
    premium_data = get_premium_request_usage(config, scope, name)
    premium_items = filter_usage_items(premium_data, args.product)

    # 计算费用
    cost = compute_cost_summary(usage_items, premium_items)

    # 计算预估
    forecast = compute_forecast(cost["total_net_amount"])

    # 输出报告
    print_report(scope, name, args.product, cost, forecast)


if __name__ == "__main__":
    main()
