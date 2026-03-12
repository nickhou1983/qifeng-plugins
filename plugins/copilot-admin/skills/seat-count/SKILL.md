---
name: seat-count
description: "查询 GitHub Copilot 已分配的许可数量及使用状态。Use when: 用户询问 Copilot 许可数、seat 数量、活跃用户数、非活跃 seat、pending 邀请数，或需要查看 Copilot 授权分配报告。支持组织级和企业级查询。"
---

# Seat Count — GitHub Copilot 许可数量查询

查询 GitHub Copilot 已分配的许可（seat）数量及使用状态。支持组织级（Organization）和企业级（Enterprise）两种查询模式，通过 `--scope` 参数切换。

## 触发场景

- 用户询问"Copilot 分配了多少个 license / seat"
- 用户想查看 Copilot 活跃用户数、非活跃用户数
- 用户询问 Copilot pending 邀请或待取消的 seat 数量
- 用户需要一份 Copilot 授权分配状态报告
- 用户需要查看哪些 seat 长期不活跃（帮助降本）
- 用户需要查看企业级 Copilot 许可概况

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

### Step 2: 查询许可统计

**组织级查询（默认）：**

```bash
python ./scripts/get_copilot_seats.py --scope org --org <组织名>
```

**企业级查询：**

```bash
python ./scripts/get_copilot_seats.py --scope enterprise --enterprise <企业名>
```

**查看 Top 5 非活跃 seat 明细：**

```bash
python ./scripts/get_copilot_seats.py --scope org --org <组织名> --top-inactive 5
```

**仅查看汇总，不输出非活跃明细：**

```bash
python ./scripts/get_copilot_seats.py --scope org --org <组织名> --top-inactive 0
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--scope` | 否 | `org` | 查询范围：`org`（组织级）或 `enterprise`（企业级） |
| `--org` | 否 | 环境变量 `GITHUB_ORG` | 组织名称（scope=org 时使用） |
| `--enterprise` | 否 | 环境变量 `GITHUB_ENTERPRISE` | 企业 slug（scope=enterprise 时使用） |
| `--top-inactive` | 否 | `10` | 显示 Top N 非活跃 seat 明细；设为 0 跳过明细输出 |

### Step 3: 解读输出

脚本会输出以下信息：

**组织级输出：**
- `total`：已分配的 seat 总数
- `active_this_cycle`：本计费周期活跃的 seat 数
- `inactive_this_cycle`：本计费周期不活跃的 seat 数
- `pending_invitation`：待接受邀请的 seat 数
- `pending_cancellation`：待取消的 seat 数
- Top N 非活跃 seat 明细（按 last_activity_at 升序排列）

**企业级输出：**
- `total_seats`：已分配的 seat 总数
- `active`：有活动记录的 seat 数（脚本从 seats 列表统计）
- `pending_cancellation`：待取消的 seat 数（脚本从 seats 列表统计）
- Top N 非活跃 seat 明细

## 注意事项

- GitHub Copilot User Management API 处于 **public preview**，字段可能随版本变更
- 企业级端点返回的数据结构与组织级不同：企业端点无 `seat_breakdown` 摘要字段，脚本会自行从 seats 列表中统计
- 企业级端点 **不支持 Fine-grained PAT**，必须使用 PAT (classic)
- 分页查询默认每页 100 条，脚本会自动遍历所有页面
