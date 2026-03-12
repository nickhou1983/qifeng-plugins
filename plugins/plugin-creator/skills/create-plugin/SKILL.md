---
name: create-plugin
description: "在 qifeng-plugins 仓库中创建新的 GitHub Copilot 插件。Use when: 用户想新增一个 Copilot 插件、创建插件骨架、生成 SKILL.md / plugin.json / README，或提到 scaffold plugin、create plugin、新建插件。"
---

# Create Plugin — GitHub Copilot 插件脚手架生成器

根据用户需求，在 `plugins/` 目录下创建一个完整的、符合本仓库约定的 Copilot 插件。

## 触发场景

- 用户说"帮我创建一个新插件"或"新建一个 plugin"
- 用户描述了某个功能，希望封装为 Copilot 插件
- 用户提到 scaffold / create / 生成插件骨架
- 用户想为现有插件添加新的 skill

## 前置要求

- 本仓库根目录位于用户工作区
- 有文件写入权限

## 仓库约定（必须遵守）

### 1. 目录结构

每个插件位于 `plugins/<plugin-name>/`，标准布局如下：

```text
plugins/<plugin-name>/
├── .github/
│   └── plugin/
│       └── plugin.json        # 必需 — 插件元数据
├── README.md                  # 必需 — 插件说明文档
├── .env.example               # 可选 — 仅当有脚本需要环境变量时
├── skills/
│   ├── <skill-name>/
│   │   ├── SKILL.md           # 必需 — 技能定义
│   │   ├── requirements.txt   # 可选 — 仅当有 Python 脚本时
│   │   └── scripts/
│   │       └── <script>.py    # 可选 — 脚本文件
│   └── common/                # 可选 — 仅当多技能共享逻辑时
│       ├── __init__.py
│       └── <shared>.py
```

**命名规范**：
- 插件名和技能名统一使用 **kebab-case**（如 `copilot-admin`、`seat-count`）
- Python 脚本文件使用 **snake_case**（如 `get_copilot_seats.py`）

### 2. plugin.json 格式

文件路径: `plugins/<plugin-name>/.github/plugin/plugin.json`

```json
{
  "name": "<plugin-name>",
  "description": "英文简短描述，一句话说明插件功能。",
  "version": "1.0.0",
  "author": {
    "name": "Qifeng Hou",
    "url": "https://github.com/nickhou1983"
  },
  "repository": "https://github.com/nickhou1983/qifeng-plugins",
  "license": "MIT",
  "keywords": [
    "github-copilot",
    "<keyword-1>",
    "<keyword-2>"
  ],
  "skills": [
    "./skills/<skill-name>"
  ]
}
```

**注意**：
- `description` 用英文书写
- `keywords` 第一个元素始终为 `"github-copilot"`
- `skills` 数组列出所有技能的相对路径

### 3. SKILL.md 格式

文件路径: `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`

```markdown
---
name: <skill-name>
description: "功能描述（中英文均可）。Use when: 列出所有触发条件，用逗号分隔，覆盖中英文触发词。"
---

# <Skill Name> — 中文副标题

一句话说明这个技能做什么。

## 触发场景

- 条件 1
- 条件 2
- 条件 3

## 前置要求

- 列出环境要求、需要的 token / API key 等

## 工作流程

### Step 1: 收集信息
向用户确认必要参数...

### Step 2: 执行操作
执行核心逻辑...

### Step 3: 输出结果
以合适的格式展示结果...

## 参数说明（如有脚本）

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| --example | 否 | - | 示例参数 |

## 注意事项

- 重要限制和注意点
```

**description 字段写法指南**：
- 必须包含 `Use when:` 标记
- 在 `Use when:` 后列出所有应触发此技能的场景
- 同时覆盖中英文触发词，用逗号分隔
- 示例：`"管理 Copilot 席位。Use when: 查询席位、license、seat count、allocation、许可证分配。"`

### 4. README.md 格式

文件路径: `plugins/<plugin-name>/README.md`

```markdown
# <Plugin Name> — 中文副标题

一段话描述插件用途。

## 包含技能

| 技能 | 说明 |
|------|------|
| **<skill-1>** | 功能说明 |
| **<skill-2>** | 功能说明 |

## 快速使用

描述典型用法示例...

## 前置配置（如需要）

环境变量或 token 配置说明...

## 许可证

MIT
```

### 5. .env.example 格式（仅当有脚本需要环境变量时）

```bash
# <Plugin Name> 环境变量
# 复制本文件为 .env 并填入实际值

# 必填项
SOME_TOKEN=your_token_here  # 获取方式说明

# 可选项
OPTIONAL_VAR=default_value  # 用途说明
```

### 6. Python 脚本约定（仅当技能需要脚本时）

```python
#!/usr/bin/env python3
"""脚本功能的一句中文描述"""

import argparse
import json
import os
import sys

# 如果需要引用 common 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "common"))

from dotenv import load_dotenv

def main():
    parser = argparse.ArgumentParser(description="脚本功能描述")
    parser.add_argument("--param", required=True, help="参数说明")
    args = parser.parse_args()

    # 加载 .env
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
    load_dotenv(env_path)

    token = os.getenv("SOME_TOKEN")
    if not token:
        print("错误：未设置 SOME_TOKEN 环境变量。", file=sys.stderr)
        print("请复制 .env.example 为 .env 并填入 token。", file=sys.stderr)
        sys.exit(1)

    # 核心逻辑...

    # 输出 JSON 格式结果
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

**脚本规范要点**：
- Shebang 行: `#!/usr/bin/env python3`
- 使用 `argparse` 解析命令行参数
- 使用 `python-dotenv` 从 `.env` 加载环境变量
- `.env` 路径通过 `__file__` 相对定位到插件根目录
- 共享模块通过 `sys.path.insert` 导入
- 错误信息用中文，输出到 `stderr`
- 正常结果用 `json.dumps()` 输出到 `stdout`
- 使用 `ensure_ascii=False` 保证中文正常显示

**requirements.txt**（与脚本放在同一技能目录下）：

```text
requests>=2.28.0
python-dotenv>=1.0.0
```

根据实际需要增减依赖。

### 7. marketplace.json 注册

创建插件后，必须在仓库根目录 `.github/plugin/marketplace.json` 的 `plugins` 数组中添加条目：

```json
{
  "name": "<plugin-name>",
  "source": "<plugin-name>",
  "description": "英文描述，与 plugin.json 中的 description 保持一致。",
  "version": "1.0.0"
}
```

## 技能分类指南

创建技能前，先判断类型：

| 类型 | 特征 | 需要脚本？ | 示例 |
|------|------|-----------|------|
| **纯指导型** | 提供模板、规范、工作流指引 | 否 | author（视频描述生成）|
| **脚本执行型** | 调用 API、处理数据、生成文件 | 是 | seat-count（查询 API）|
| **混合型** | 指导 + 脚本 | 是 | video-gen（指导 + 调 API）|

## 工作流程

### Step 1: 收集信息

向用户确认以下要素（如果用户未明确提供）：

1. **插件名称**：用 kebab-case（例如 `code-review`、`issue-tracker`）
2. **插件功能描述**：一句话说明做什么（中文），另备一句英文用于 `plugin.json`
3. **包含的技能列表**：每个技能的名称和简要说明
4. **技能类型**：每个技能是纯指导型、脚本执行型还是混合型
5. **是否需要环境变量**：如 API Token、组织名等
6. **是否有多技能共享逻辑**：决定是否需要 `common/` 目录

### Step 2: 生成文件

按以下顺序创建文件：

1. `plugins/<plugin-name>/.github/plugin/plugin.json` — 插件元数据
2. `plugins/<plugin-name>/README.md` — 插件文档
3. 对于每个技能：
   - `plugins/<plugin-name>/skills/<skill-name>/SKILL.md` — 技能定义
   - （如果是脚本执行型/混合型）`requirements.txt` + `scripts/<script>.py`
4. （如果需要环境变量）`plugins/<plugin-name>/.env.example`
5. （如果有共享模块）`plugins/<plugin-name>/skills/common/__init__.py` + 共享代码

### Step 3: 注册插件

在 `.github/plugin/marketplace.json` 的 `plugins` 数组末尾追加新插件条目。

### Step 4: 验证

- 检查所有文件已创建且路径正确
- 如有 Python 脚本，用 `python3 -m py_compile <script>.py` 验证语法
- 确认 `marketplace.json` 格式正确（有效 JSON）
- 列出完整文件树供用户确认

## 注意事项

- **不要修改**其他已有插件的文件
- **author 信息固定**为 `Qifeng Hou` / `https://github.com/nickhou1983`
- **license 固定**为 MIT
- **repository 固定**为 `https://github.com/nickhou1983/qifeng-plugins`
- 如果用户没有指定版本号，默认使用 `1.0.0`
- SKILL.md 的 `description` 字段要尽量覆盖多种触发词，包括中英文同义词
- 生成脚本时，参考仓库中现有脚本的风格和结构（如 `get_copilot_seats.py`）
