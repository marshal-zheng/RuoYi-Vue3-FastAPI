---
name: init-ai-workspace
description: Use when initializing a new AI-assisted development workspace, setting up standardized .cursor skills/commands, docs structure, and AGENTS.md, or when onboarding a project to AI-first development workflow.
---

# Init AI Workspace

Bootstrap a standardized AI development workspace with skills, commands, documentation scaffolding, and project guidelines.

## Language Policy

- Skill content: English
- User dialogue: 中文 (Chinese)

## Workflow

### Phase 1: Brief Introduction

Present this overview to the user (in Chinese):

> **AI 工作区标准化结构**
>
> | 结构 | 用途 | 状态 |
> |------|------|------|
> | `.cursor/skills/` | Agent 技能库 — 行为模式和工作流 | 必须 |
> | `.cursor/commands/` | 快捷命令 — 常用操作入口 | 必须 |
> | `docs/codemaps/` | 代码地图 — 架构概览 | 必须 |
> | `docs/plans/` | 实现计划 — 执行规划 | 必须 |
> | `docs/specs/` | 规格文档 — 需求/设计/任务规范 | 必须 |
> | `docs/learned/` | 经验沉淀 — 可复用模式和教训 | 推荐 |
> | `FAQ/` | 常见问题库 — 问题解决方案索引 | 推荐 |
> | `AGENTS.md` | 项目指南 — Agent 全局行为准则 | 必须 |
>
> **必须 Skills（6 个，通过 @tdio/skills 自动安装）：**
> `brainstorming` · `skill-loader` · `update-codemaps` · `writing-plans` · `writing-skills` · `writing-specs`
>
> **可选 Skills（需确认）：**
> `frontend-conventions` · `backend-conventions`

### Phase 2: Collect Information

Use `AskQuestion` tool. If unavailable, ask conversationally.

**Q1 — Optional skills (multi-select):**

```
Prompt: "是否需要以下开发规范 Skill？（可多选）"
Options:
  - frontend-conventions — 前端开发规范
  - backend-conventions — 后端开发规范
  - none — 都不需要
Allow multiple: true
```

**Q2 — Recommended directories (multi-select):**

```
Prompt: "以下推荐目录是否需要？（可多选）"
Options:
  - docs/learned/ — 沉淀 AI 会话中的可复用模式，避免重复踩坑，是 Agent 的长期记忆
  - FAQ/ — 团队共享的常见问题解决方案索引
  - none — 都不需要
Allow multiple: true
```

**Q3 — Project info (conversational):**

Ask: "请简要描述你的项目：1) 项目名称 2) 技术栈（如 Vue3 + FastAPI）3) 主要模块目录结构"

### Phase 3: Run Init Script

Based on Q1 and Q2 answers, build the script arguments and run:

```bash
node .cursor/skills/init-ai-workspace/scripts/init.js [OPTIONS]
```

Options mapping:
- Q1 selected `frontend-conventions` → `--frontend`
- Q1 selected `backend-conventions` → `--backend`
- Q2 selected `docs/learned/` → `--learned`
- Q2 selected `FAQ/` → `--faq`

Example (user selected frontend + learned):
```bash
node .cursor/skills/init-ai-workspace/scripts/init.js --frontend --learned
```

The script will:
1. Install/update required skills from remote repo via `@tdio/skills` CLI (existing = update, missing = install)
2. Copy command files from `assets/` to `.cursor/commands/` (skip existing)
3. Create required `docs/` directories (codemaps, plans, specs)
4. Create optional directories based on flags

### Phase 4: Generate AGENTS.md

Read `reference/agents-template.md`. Generate `AGENTS.md` at project root using user's project info from Q3.

**If `AGENTS.md` already exists:** ask user whether to overwrite, merge, or skip.

### Phase 5: Post-Init Guidance

After script completes, remind user (in Chinese):

> **接下来你需要：**
>
> 1. 根据项目实际情况完善 `AGENTS.md`
> 2. 已安装的 Skills 可随时通过 `npx @tdio/skills check` 检查更新

## File Layout

```
init-ai-workspace/
├── SKILL.md                          # This file
├── assets/
│   └── commands/                     # Command templates (copied to .cursor/commands/)
│       ├── faq.md
│       ├── learn.md
│       ├── skill-stubs.md            # Reference: skill descriptions and minimal templates
│       ├── task-alignment-review.md
│       └── update-codemaps.md
├── reference/
│   └── agents-template.md            # AGENTS.md generation template
└── scripts/
    ├── init.js                       # Workspace bootstrap script (orchestrator)
    └── install-skills.js             # Skill install/update via @tdio/skills CLI
```

## Rules

- **Never overwrite existing files** — script skips existing commands
- **All user dialogue in Chinese**
- **Ask before creating** — complete Phase 1-2 before running script
- **Skills via CLI** — use `@tdio/skills` to install/update, never create stubs manually
- **AGENTS.md** — the only file the agent generates (not the script)

## Common Mistakes

- Manually creating SKILL.md stubs instead of using `@tdio/skills` CLI
- Running script before completing user interaction (Phase 1-2)
- Generating AGENTS.md without project-specific info from Q3
- Using English in user dialogue instead of Chinese
- Overwriting existing command files
