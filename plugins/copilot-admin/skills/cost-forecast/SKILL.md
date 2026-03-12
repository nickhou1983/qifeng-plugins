---
name: cost-forecast
description: "查询 GitHub Copilot 当前费用和预估月底费用。Use when: 用户询问 Copilot 费用、花费、账单、billing、cost、当月累计费用、月底预估费用，或需要查看 Copilot 成本报告。支持组织级和企业级查询。"
---

# Cost Forecast — GitHub Copilot 费用与预估查询

查询 GitHub Copilot 当前累计费用，并根据已过天数线性外推预估月底总费用。支持组织级（Organization）和企业级（Enterprise）两种查询模式，通过 `--scope` 参数切换。支持 `--product` 参数过滤指定产品（默认 Copilot）。

## 触发场景

- 用户询问"Copilot 费用多少 / 花了多少钱"
- 用户想查看本月 Copilot 累计账单
- 用户询问本月 Copilot 预估总费用 / 月底费用
- 用户需要一份 Copilot 成本报告或费用趋势
- 用户需要查看企业级 Copilot 费用概况
- 用户想查看 Copilot Premium Requests 的费用明细

## 前置要求

1. 拥有目标组织或企业的 GitHub PAT（Personal Access Token）
2. 在 Skill 目录下配置 `.env` 文件（参考 [.env.example](../../.env.example)）
3. 已安装 Python 3.10+、`requests` 和 `python-dotenv`

**权限要求：**
- **Organization 模式**：`manage_billing:copilot` 或 `read:org` 权限（Fine-grained PAT 可用）
- **Enterprise 模式**：PAT (classic) + `manage_billing:copilot` 或 `read:enterprise` 权限（⚠️ Fine-grained PAT 不支持企业级端点）

安装依赖：

```bash
pip install -r ./requirements.txt
```

## 环境配置

复制插件根目录下的 `.env.example` 为 `.env` 并填入实际配置：

```text
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_ORG=your-org-name
GITHUB_ENTERPRISE=your-enterprise-slug
```

确保 `.env` 不被提交到版本控制。

## 工作流程

### Step 1: 确认查询范围

确认用户需要查询的是组织级（org）还是企业级（enterprise）数据。

### Step 2: 查询费用

**组织级查询（默认）：**

```bash
python ./scripts/get_copilot_costs.py --scope org --org <组织名>
```

**企业级查询：**

```bash
python ./scripts/get_copilot_costs.py --scope enterprise --enterprise <企业名>
```

**指定过滤产品（默认为 Copilot）：**

```bash
python ./scripts/get_copilot_costs.py --scope org --org <组织名> --product "Copilot"
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--scope` | 否 | `org` | 查询范围：`org`（组织级）或 `enterprise`（企业级） |
| `--org` | 否 | 环境变量 `GITHUB_ORG` | 组织名称（scope=org 时使用） |
| `--enterprise` | 否 | 环境变量 `GITHUB_ENTERPRISE` | 企业 slug（scope=enterprise 时使用） |
| `--product` | 否 | `Copilot` | 按产品名称过滤 usageItems（大小写不敏感匹配） |

### Step 3: 解读输出

脚本会输出以下信息：

- **当前累计费用**：本月已产生的 Copilot 相关 netAmount 总额（含基础订阅 + Premium Requests）
- **日均费用**：当前累计 / 已过天数
- **月底预估费用**：日均费用 × 当月总天数
- **Premium Requests 费用明细**：各模型的用量、单价与金额
- **口径说明**：数据来源与计算方式

**预估公式：**

```
月底预估费用 = 当前累计费用 / 本月已过天数 × 本月总天数
```

## 注意事项

- GitHub Billing Usage API 处于 **public preview**，字段可能随版本变更
- 预估费用基于线性外推，假设后续日均用量与当前一致，仅供参考
- 月初第 1 天的预估值可能偏差较大（仅有不到 1 天的数据）
- `--product` 参数执行大小写不敏感的包含匹配，例如 "Copilot" 同时匹配 "GitHub Copilot Business" 和 "Copilot Premium Requests"
- 企业级端点 **不支持 Fine-grained PAT**，必须使用 PAT (classic)
