---
name: writing-specs
description: "Use when the user needs a formal feature specification package before implementation, or when an existing spec package must be resumed or updated."
---

# Writing Specs (Execution Contract)

Generate and maintain a three-file spec package with explicit tool actions, verifiable outputs, and phase gates.

**Announce at start:** "Using writing-specs skill to generate specification documents."
**Language:** Generated markdown files (`requirements.md`, `design.md`, `tasks.md`) must be in Chinese.

## When to Use

Use this skill when:
- A feature requires a formal three-file spec package before implementation.
- Existing spec work in `docs/specs/<feature-name>/` must be resumed or updated.
- The user asks for explicit requirement IDs, traceability, and approval gates.

Do not use this skill when:
- The user only asks for a minor text edit to an existing spec file.
- The user requests direct implementation with no spec phase.

## Required Tool Actions (Must Execute)

For each phase, do not stop at advice. Execute these actions:

1. **Read files**: inspect existing spec files and project context (`AGENTS.md`, relevant code).
2. **Search code**: use code search (prefer `rg`) to collect evidence for design and task decisions.
3. **Run commands**: run lightweight verification commands for structure and traceability.
4. **Write files**: create or update the target spec file for the current phase.
5. **Output report**: return the required output schema with evidence and next action.

## Response Constraints (Token Efficiency)

- No long preambles, no verbose planning narrative.
- Focus on mandatory actions, concrete outputs, and evidence.
- Ask at most one blocking clarification if critical information is missing.
- Avoid repeating static rules in every message.

## Spec Location and Resume Policy

Output folder:

```
docs/specs/<feature-name>/
├── requirements.md
├── design.md
└── tasks.md
```

Resume behavior:

1. If folder does not exist, create it and start at Phase 1.
2. If folder exists, read current files and continue from the first incomplete phase.
3. Never overwrite an approved phase unless user explicitly requests revision.
4. If user requests a full restart, create the next available versioned folder: `docs/specs/<feature-name>-v<N>/`.

Versioning rule for restarts:
- Scan existing folders matching `<feature-name>-v<number>`.
- Choose `N = max(existing version numbers) + 1`.
- If no versioned folder exists, start with `N = 2`.

Incomplete phase definition:
- `requirements.md` missing or not explicitly approved.
- `design.md` missing or not explicitly approved.
- `tasks.md` missing.

## Output Schema (Required Every Turn)

Use this exact structure after each phase action:

```markdown
STATUS: <one of: REQUIREMENTS_DRAFTED | WAITING_REQUIREMENTS_APPROVAL | DESIGN_DRAFTED | WAITING_DESIGN_APPROVAL | TASKS_DRAFTED | BLOCKED>
FILES_WRITTEN:
- <path or "none">
EVIDENCE:
- READ: <files inspected>
- SEARCH: <queries and key hits>
- COMMAND: <commands run and pass/fail>
NEXT_ACTION: <single concrete next action>
GATE_MESSAGE: <exact gate phrase or "none">
BLOCK_REASON: <required when STATUS=BLOCKED, otherwise "none">
UNBLOCK_ACTION: <required when STATUS=BLOCKED, otherwise "none">
```

## Blocked State Rules (Required)

Enter `BLOCKED` only when at least one condition is true:

1. A critical input is missing and cannot be inferred after one blocking clarification.
2. A required verification command fails and cannot be fixed in the current turn.
3. Required files are inaccessible due to path or permission constraints.

When `STATUS=BLOCKED`:

- `FILES_WRITTEN` must be `"none"` unless partial output is explicitly requested.
- `BLOCK_REASON` must describe the concrete blocker.
- `UNBLOCK_ACTION` must contain exactly one action the user can take next.
- `GATE_MESSAGE` must be `"none"`.

Exit `BLOCKED` only after blocker resolution, then resume from the same phase.

## Minimum Verification Commands (Required)

Use `<spec-dir>=docs/specs/<feature-name>` in commands below.

Phase 1 (`requirements.md`) checks:

- `test -f <spec-dir>/requirements.md`
- `rg -n "^# .+需求规格$" <spec-dir>/requirements.md`
- `rg -n "^### R[0-9]+:" <spec-dir>/requirements.md`
- `rg -n "R[0-9]+\\.AC[0-9]+:" <spec-dir>/requirements.md`
- `dups=$(rg -o "R[0-9]+\\.AC[0-9]+" <spec-dir>/requirements.md | sort | uniq -d); test -z "$dups"`

Pass criteria:
- All commands succeed.
- Duplicate AC ID check returns empty.

Phase 2 (`design.md`) checks:

- `test -f <spec-dir>/design.md`
- `rg -n "^# .+技术设计$" <spec-dir>/design.md`
- `rg -n "^## 架构概述$" <spec-dir>/design.md`
- `rg -n "^## 数据流图$" <spec-dir>/design.md`
- `rg -n "^## 组件与接口定义$" <spec-dir>/design.md`
- `rg -n "^## API 接口设计$" <spec-dir>/design.md`
- `rg -n "^## 数据模型与数据库变更$" <spec-dir>/design.md`
- `rg -n "^## 安全考量$" <spec-dir>/design.md`
- `rg -n "^## 测试策略$" <spec-dir>/design.md`

Pass criteria:
- All commands succeed.

Phase 3 (`tasks.md`) checks:

- `test -f <spec-dir>/tasks.md`
- `rg -n "^# .+实现任务$" <spec-dir>/tasks.md`
- `rg -n "_需求追溯: " <spec-dir>/tasks.md`
- `rg -o "R[0-9]+\\.AC[0-9]+" <spec-dir>/tasks.md | sort -u > /tmp/spec-task-refs.txt`
- `rg -o "R[0-9]+\\.AC[0-9]+" <spec-dir>/requirements.md | sort -u > /tmp/spec-req-refs.txt`
- `comm -23 /tmp/spec-task-refs.txt /tmp/spec-req-refs.txt`

Pass criteria:
- All commands succeed.
- `comm -23` output is empty.

## Evidence Minimums (Required)

Evidence must include repository-relative file paths, and include line numbers when available.

Phase 1 minimum evidence:
- READ: at least 1 project context file and any existing spec file in `<spec-dir>`.
- SEARCH: at least 1 query relevant to domain terms in the feature request.

Phase 2 minimum evidence:
- READ: `requirements.md` plus at least 2 relevant repository files.
- SEARCH: at least 2 queries.
- Include at least 2 concrete search hits with `path:line`.

Phase 3 minimum evidence:
- READ: approved `requirements.md` and `design.md`.
- SEARCH: at least 1 query for dependency/order validation.
- Include at least 1 concrete search hit with `path:line`.

## Phase 1: Requirements (`requirements.md`)

Actions:

1. Read existing spec files (if any) and relevant project context.
2. Write `requirements.md` in Chinese with stable IDs and EARS criteria.
3. Run quick checks for ID presence and format.
4. Emit phase report with exact approval gate phrase.

Requirements format:

```markdown
# <功能名称> 需求规格

## 简介
...

## 需求列表

### R1: <需求标题>
**用户故事:** 作为 <角色>，我希望 <能力>，以便 <价值>
**验收标准 (EARS):**
- R1.AC1: WHEN ...
- R1.AC2: IF ...

### R2: <需求标题>
...
```

ID rules:
- Requirement IDs: `R<number>`.
- Acceptance criteria IDs: `R<number>.AC<number>`.
- IDs are immutable after approval.

Success signals:
- `requirements.md` exists.
- At least one requirement with at least one AC.
- AC IDs are unique and match `R#.AC#`.
- Gate message is emitted exactly.

Approval gate phrase (exact):
`requirements.md has been generated. Are the requirements correct? After approval, I will proceed to the technical design phase.`

## Phase 2: Design (`design.md`)

Precondition: requirements explicitly approved.

Actions:

1. Read approved `requirements.md`.
2. Search relevant code and reference concrete files/components.
3. Write `design.md` in Chinese, grounded in requirements and code evidence.
4. Run lightweight checks that major sections exist.
5. Emit phase report with exact approval gate phrase.

Design minimum sections:
- 架构概述
- 数据流图（Mermaid）
- 组件与接口定义
- API 接口设计
- 数据模型与数据库变更
- 安全考量
- 测试策略

Success signals:
- `design.md` exists.
- Each minimum section exists.
- Design references real project context from read/search evidence.
- Gate message is emitted exactly.

Approval gate phrase (exact):
`design.md has been generated. Is the technical design correct? After approval, I will proceed to the task breakdown phase.`

## Phase 3: Tasks (`tasks.md`)

Precondition: design explicitly approved.

Actions:

1. Read approved `requirements.md` and `design.md`.
2. Write `tasks.md` in Chinese and in dependency order.
3. Map every task block to existing AC IDs.
4. Run traceability checks (`tasks.md` references must exist in `requirements.md`).
5. Emit phase report with completion message.

Tasks format rules:
- High-level tasks: `- [ ] N. 任务描述`
- Sub-tasks: indented `- 具体步骤`
- End each task block with `_需求追溯: R#.AC#, ..._`

Success signals:
- `tasks.md` exists.
- Every `_Traceability` reference maps to an existing AC ID.
- No orphan AC references.
- Completion signal emitted exactly.

Completion signal (exact):
`Implementation tasks have been generated. You can start executing Task 1 when ready.`

## Enforcement Rules

- Never skip phase order: requirements -> design -> tasks.
- Never proceed from Phase 1 or 2 without explicit user approval.
- If user requests changes, update the current phase file and re-emit the same gate phrase.
- Act with tools and evidence; do not return suggestion-only responses.
- Keep all natural-language content in generated markdown files in Chinese (keep IDs, paths, and code identifiers unchanged).

## Common Failure Modes (Preventive)

- Drafting `design.md` before explicit requirements approval.
- Missing exact gate phrase after a phase write.
- Returning generic evidence without concrete file paths or search hits.
- Producing task traceability IDs that do not exist in `requirements.md`.
- Entering `BLOCKED` without a single concrete `UNBLOCK_ACTION`.
