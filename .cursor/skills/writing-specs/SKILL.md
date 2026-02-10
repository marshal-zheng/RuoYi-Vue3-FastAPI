---
name: writing-specs
description: "Generate structured feature specs (requirements, design, tasks) following Kiro-style spec-driven workflow. Use after brainstorming or when the user wants to create feature specifications."
---

# Writing Specs (Kiro-Style Spec-Driven Workflow)

Implement Kiro IDE 的三阶段 spec-driven 开发流程，将功能想法转化为结构化的规格文档。

**Announce at start:** "正在使用 writing-specs skill 来生成规格文档。"

**All spec file content and dialogue must be in Chinese.**

## Output Structure

```
docs/specs/<feature-name>/
├── requirements.md   # Phase 1: 用户故事 + EARS 验收标准
├── design.md         # Phase 2: 技术架构设计
└── tasks.md          # Phase 3: 实现任务分解
```

## Phase 1: Requirements (requirements.md)

**Trigger:** User provides a feature idea (directly or via brainstorming handoff).

**Behavioral Rules:**
- Do NOT ask multiple clarifying questions before generating first draft
- Proactively think through scenarios, edge cases, error conditions
- Produce a comprehensive first draft as a concrete discussion basis

**Format:**

```markdown
# <功能名称> 需求规格

## 简介
[功能要解决的问题和目标概述]

## 需求列表

### 需求 1
**用户故事:** 作为 [角色]，我希望 [功能]，以便 [价值]

**验收标准 (EARS):**
1. WHEN [条件] THE SYSTEM SHALL [行为]
2. IF [条件] THEN THE SYSTEM SHALL [行为]
3. WHILE [状态] THE SYSTEM SHALL [行为]

### 需求 2
**用户故事:** 作为 [角色]，我希望 [功能]，以便 [价值]

**验收标准 (EARS):**
1. WHEN [条件] THE SYSTEM SHALL [行为]
```

**Write file → approval gate (exact phrase):**

> "requirements.md 已生成。需求内容是否正确？确认后我将进入技术设计阶段。"

**If user requests changes:** update file → ask approval again with same phrase.

**Do NOT proceed to Phase 2 without explicit approval.**

## Phase 2: Design (design.md)

**Trigger:** User explicitly approves requirements.

**Before generating, synthesize three sources:**
1. Approved `requirements.md`
2. Project context (AGENTS.md, existing codebase structure)
3. Static analysis of relevant existing code

**Format:**

```markdown
# <功能名称> 技术设计

## 架构概述
[整体方案，如何融入现有系统]

## 数据流图
[使用 Mermaid.js 语法的数据流程图]

## 组件与接口定义
### 组件 A
- 职责: ...
- 接口定义: ...

## API 接口设计
### [HTTP方法] [路径]
- 请求体: ...
- 成功响应: ...
- 错误响应: ...

## 数据库变更
[表结构 / DDL / ORM 模型变更（如适用）]

## 安全考量
[潜在风险分析与缓解策略]

## 测试策略
[单元测试、集成测试、E2E 测试覆盖范围]
```

**Write file → approval gate (exact phrase):**

> "design.md 已生成。技术设计是否正确？确认后我将进入任务分解阶段。"

**If user requests changes:** update file → ask approval again with same phrase.

**Do NOT proceed to Phase 3 without explicit approval.**

## Phase 3: Tasks (tasks.md)

**Trigger:** User explicitly approves design.

**Before generating, read and synthesize:**
1. Approved `requirements.md` and `design.md`
2. Project context (AGENTS.md, coding conventions)

**Format:**

```markdown
# <功能名称> 实现任务

- [ ] 1. [高级目标描述]
  - 具体子任务 A
  - 具体子任务 B
  - 具体子任务 C
  - _需求追溯: 1.1, 1.2_

- [ ] 2. [高级目标描述]
  - 具体子任务 A
  - 具体子任务 B
  - _需求追溯: 2.1_

- [ ] 3. [高级目标描述]
  - 具体子任务 A
  - 具体子任务 B
  - _需求追溯: 1.3, 2.2_
```

**Rules:**
- High-level tasks formatted as `- [ ] N. Description`
- Sub-tasks indented as `- Description`
- Logical execution order, respecting dependencies
- Each task block ends with `_需求追溯: [requirement.AC numbers]_`

**Write file → completion signal (exact phrase, NO approval gate):**

> "实现任务已生成。准备好后可以开始执行第一个任务。"

## Key Rules Summary

1. **Sequential phases** — requirements → design → tasks, never skip or batch
2. **Approval gates** — Phase 1 and Phase 2 require explicit user approval before proceeding
3. **No gate on Phase 3** — tasks.md generates and signals readiness directly
4. **Proactive first drafts** — don't ask clarifying questions, generate comprehensive drafts
5. **Iterative feedback** — update file on feedback, re-ask approval with same phrase
6. **Chinese** — all dialogue and file content in Chinese
