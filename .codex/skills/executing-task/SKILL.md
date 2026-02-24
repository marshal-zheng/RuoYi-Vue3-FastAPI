---
name: executing-task
description: "Execute tasks from a tasks.md spec file with mandatory context verification and progress tracking. Use when specs are complete and ready for implementation."
---

# Executing Tasks (Kiro-Style)

Load spec, verify comprehension, execute tasks with progress tracking. Follows Kiro IDE's executeTask workflow.

**Announce at start:** "正在使用 executing-task skill 来执行实现任务。"

## User Commands

User controls execution via commands:
- **`implement`** — start/continue from the next unchecked task
- **`continue`** — continue to the next task after current one completes
- **`implement N`** — jump to and execute task N specifically

## Mandatory Process (Per Task)

### 1. Context Gathering (First Task Only)

Read ALL spec documents before starting:
- `docs/specs/<feature-name>/requirements.md`
- `docs/specs/<feature-name>/design.md`
- `docs/specs/<feature-name>/tasks.md`
- Project context: `AGENTS.md`, relevant existing code

### 2. Comprehension Verification (First Task Only)

Before writing any code, summarize understanding:

> **文档理解确认：**
> - 需求概述: [一句话]
> - 技术方案: [关键设计决策]
> - 当前任务: Task N — [描述]
> - 涉及文件: [将创建/修改的文件列表]
> - 实现思路: [具体方案说明]

Wait for user confirmation before proceeding.

### 3. Execute Task

1. Follow task steps exactly
2. Run verifications as specified
3. Update `tasks.md` — mark checkbox as `[x]`

### 4. Report Completion

Each task complete:

> "Task N 已完成。[简述做了什么]。输入 `continue` 继续下一个任务。"

### 5. All Tasks Complete

> "所有任务已完成。是否需要使用 `finishing-a-development-branch` skill 来收尾？"

## When to Stop

**STOP immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Spec has critical gaps
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## Remember

- Read full spec before starting, not just tasks.md
- Summarize understanding and get confirmation before first task
- Follow task steps exactly
- Don't skip verifications
- Update tasks.md checkboxes as tasks complete
- Stop when blocked, don't guess
- Never start on main/master without explicit user consent

## Integration

**Related skills:**
- `writing-specs` — creates the specs this skill executes
- `using-git-worktrees` — set up isolated workspace before starting
- `finishing-a-development-branch` — complete development after all tasks
