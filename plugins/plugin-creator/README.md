# Plugin Creator — GitHub Copilot 插件脚手架

一键创建符合本仓库约定的 GitHub Copilot 插件骨架，包含目录结构、`plugin.json`、`SKILL.md`、`README.md` 以及可选的 Python 脚本模板。

## 包含技能

| 技能 | 说明 |
|------|------|
| **create-plugin** | 根据用户描述，生成完整的插件目录和文件 |

## 快速使用

在 GitHub Copilot Chat 中描述你想要创建的插件：

```text
帮我创建一个名为 code-review 的插件，用于代码审查，包含一个 review 技能，需要 Python 脚本调用 GitHub API
```

Agent 会自动生成：

```text
plugins/code-review/
├── .github/plugin/plugin.json
├── README.md
├── .env.example          # 如有脚本
├── skills/
│   └── review/
│       ├── SKILL.md
│       ├── requirements.txt   # 如有脚本
│       └── scripts/
│           └── run_review.py  # 如有脚本
└── skills/common/             # 如有多技能共享逻辑
    ├── __init__.py
    └── shared_client.py
```

并自动将插件注册到根目录的 `marketplace.json`。

## 适用场景

- 快速创建新的 Copilot 插件项目骨架
- 确保目录结构和文件格式与仓库现有约定一致
- 减少重复劳动，避免遗漏关键文件

## 许可证

MIT
