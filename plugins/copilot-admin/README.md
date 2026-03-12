# Copilot Admin Plugin

查询 GitHub Copilot 许可分配数量和计费费用，支持组织级（Organization）和企业级（Enterprise）查询。

## Skills

| Skill | Description |
|-------|-------------|
| **seat-count** | 查询 Copilot 已分配的许可数量、活跃/非活跃/待邀请/待取消统计，以及 Top N 非活跃 seat 明细 |
| **cost-forecast** | 查询 Copilot 当月累计费用，并线性外推预估月底总费用，含 Premium Requests 明细 |

## Workflow

1. **配置凭据** — 复制 `.env.example` 为 `.env`，填入 GitHub PAT 和组织名/企业名
2. **查询许可** — 使用 `seat-count` skill 了解 Copilot 许可分配与活跃状况
3. **查询费用** — 使用 `cost-forecast` skill 了解当月费用与月底预估

## Prerequisites

- Python 3.10+
- GitHub PAT（Personal Access Token）
  - **Organization 模式**：需要 `manage_billing:copilot` 或 `read:org` 权限（Fine-grained PAT 可用）
  - **Enterprise 模式**：需要 PAT (classic) + `manage_billing:copilot` 或 `read:enterprise` 权限（⚠️ Fine-grained PAT 不支持企业级端点）
- 目标组织或企业已启用 GitHub Copilot

## Installation

```bash
cd plugins/copilot-admin
cp .env.example .env
# 编辑 .env 填入你的 GitHub PAT 和组织名/企业名

# 安装依赖（两个 skill 使用相同依赖）
pip install -r skills/seat-count/requirements.txt
```

## Usage

### 查询许可数量

```bash
# 组织级查询（默认）
python skills/seat-count/scripts/get_copilot_seats.py --scope org --org my-org

# 企业级查询
python skills/seat-count/scripts/get_copilot_seats.py --scope enterprise --enterprise my-enterprise

# 查看 Top 5 非活跃 seat
python skills/seat-count/scripts/get_copilot_seats.py --scope org --org my-org --top-inactive 5

# 仅汇总，不输出明细
python skills/seat-count/scripts/get_copilot_seats.py --scope org --org my-org --top-inactive 0
```

**输出示例（组织级）：**

```text
============================================================
GitHub Copilot 许可统计报告（Organization）
============================================================
  已分配 seat 总数:       120
  本周期活跃:             98
  本周期不活跃:           15
  待接受邀请:             5
  待取消:                 2
  本周期新增:             8

Top 10 非活跃 Seat 明细:
------------------------------------------------------------
  用户                             最后活跃时间
------------------------------------------------------------
  user-a                           从未使用
  user-b                           2025-01-15T10:30:00Z
  ...
```

### 查询费用与预估

```bash
# 组织级查询（默认过滤 Copilot 产品）
python skills/cost-forecast/scripts/get_copilot_costs.py --scope org --org my-org

# 企业级查询
python skills/cost-forecast/scripts/get_copilot_costs.py --scope enterprise --enterprise my-enterprise

# 指定产品过滤
python skills/cost-forecast/scripts/get_copilot_costs.py --scope org --org my-org --product "Copilot"
```

**输出示例：**

```text
============================================================
GitHub Copilot 费用报告（Organization）
============================================================
  查询目标:               my-org
  产品过滤:               Copilot
  查询日期:               2026-03-12

费用汇总:
  基础订阅费用:           $2280.00
  Premium Requests 费用:  $156.30
  当月累计费用:           $2436.30

月底预估:
  本月已过天数:           11.5 / 31 天
  日均费用:               $211.85
  月底预估费用:           $6567.35

Premium Requests 明细:
------------------------------------------------------------
  SKU                                    数量       金额
------------------------------------------------------------
  Copilot Premium Requests - GPT-4o       1200   $  120.00
  Copilot Premium Requests - Claude         180   $   36.30

口径说明:
  - 当月累计费用 = Billing Usage Summary 中匹配产品的 netAmount 总和
    + Premium Request Usage 中匹配产品的 netAmount 总和
  - 月底预估费用 = 当月累计费用 / 已过天数 × 当月总天数（线性外推）
  - 预估值假设后续日均用量与当前一致，仅供参考
```

## Limitations

- GitHub Copilot User Management API 和 Billing Usage API 均处于 **public preview**，字段和端点可能随版本变更
- 企业级端点不返回 `seat_breakdown` 摘要，脚本从 seats 列表统计得出
- 月底预估基于线性外推，实际费用可能因用量波动而有偏差
- 月初第 1 天不足半天数据时，脚本不做预估以避免极端偏差

## License

MIT
