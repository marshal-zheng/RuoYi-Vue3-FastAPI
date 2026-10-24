---
name: writing-plans
description: Use when the task is medium-complexity and already scoped, and the user needs a lightweight execution plan before coding without creating a formal multi-file spec package.
---

# Writing Plans (Execution Contract)

Generate a single implementation plan document that is actionable, verifiable, and ready for execution.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."
**Language:** All dialogue and generated plan content must be in English.

## When to Use

Use this skill when:
- Requirements and technical design are already approved or clearly defined.
- The user needs a concrete execution sequence before writing implementation code.
- The work has multiple dependent steps and benefits from explicit order and verification.
- The change has moderate complexity and does not require full spec authoring.

Do not use this skill when:
- The problem still needs discovery or tradeoff exploration (use `brainstorming` first).
- A formal spec package is missing (use `writing-specs` first when requirements/design are not settled).
- The user explicitly requests full requirements/design/task traceability artifacts with approval gates.
- The change is a trivial one-step edit.

## Boundary With `writing-specs`

- `writing-specs`: defines **WHAT** to build (`requirements.md`, `design.md`, `tasks.md`) with approval gates.
- `writing-plans`: defines **HOW** to implement in execution order (single file in `docs/plans/`), no phase gates.

Typical flow: `brainstorming` -> `writing-specs` -> `writing-plans` -> `executing-plans`

## Required Tool Actions (Must Execute)

1. Read requirement/design context and relevant repository files.
2. Search code (prefer `rg`) to identify exact existing file paths and test locations.
3. Run lightweight discovery commands needed to validate paths and scope.
4. Write or update the plan file in `docs/plans/`.
5. Return the required output schema with evidence and next action.

## Response Constraints (Token Efficiency)

- No long preambles or verbose planning narrative.
- Prefer concrete actions, exact paths, and verification commands.
- Avoid large boilerplate code blocks unless they are necessary for correctness.
- Ask at most one blocking clarification when critical information is missing.

## Plan Location and Versioning

Primary path:

```
docs/plans/YYYY-MM-DD-<feature-name>.md
```

If the file already exists and user requests a fresh rewrite, create `docs/plans/YYYY-MM-DD-<feature-name>-v<N>.md` with incremented `N`.

## Output Schema (Required Every Turn)

Use this exact structure:

```markdown
STATUS: <one of: PLAN_DRAFTED | PLAN_UPDATED | WAITING_FEEDBACK | BLOCKED>
FILES_WRITTEN:
- <path or "none">
EVIDENCE:
- READ: <files inspected>
- SEARCH: <queries and key hits>
- COMMAND: <commands run and pass/fail>
NEXT_ACTION: <single concrete next action>
BLOCK_REASON: <required when STATUS=BLOCKED, otherwise "none">
UNBLOCK_ACTION: <required when STATUS=BLOCKED, otherwise "none">
```

## Plan Document Structure (Required)

Every plan must include:

```markdown
# <Feature Name> Implementation Plan

**Goal:** <single-sentence outcome>
**Inputs:** <approved specs/design links or file paths>
**Scope Boundaries:** <explicit in-scope and out-of-scope items>
**Assumptions:** <only if needed>

## Task List

### Task 1: <Title>

**Files:**
- Create: `<repo-relative path>` (if any)
- Modify: `<repo-relative path>` (if any)
- Test: `<repo-relative path>` (if any)

**Steps:**
1. <single action>
2. <single action>
3. <single action>

**Verification:**
- Run: `<exact command>`
- Expect: `<pass/fail signal>`

**Dependencies:** <task IDs or "none">
**Output:** <concrete artifact produced by this task>
```

Task rules:
- Use dependency order; do not reference future tasks as prerequisites.
- Each step should be one action and typically fit within 2-10 minutes.
- Include exact commands for verification.
- Include code snippets only when logic is non-trivial or error-prone.
- Do not require commits as a mandatory step unless the user explicitly asks.

## Minimum Verification Commands (Required)

Use `<plan>=docs/plans/<filename>.md`:

- `test -f <plan>`
- `rg -n "^# .*Implementation Plan$" <plan>`
- `rg -n "^## Task List$" <plan>`
- `rg -n "^### Task [0-9]+:" <plan>`
- `rg -n "^\\*\\*Files:\\*\\*$" <plan>`
- `rg -n "^\\*\\*Steps:\\*\\*$" <plan>`
- `rg -n "^\\*\\*Verification:\\*\\*$" <plan>`
- `rg -n "^\\*\\*Dependencies:\\*\\*$" <plan>`
- `rg -n "^\\*\\*Output:\\*\\*$" <plan>`

Pass criteria:
- All commands succeed.
- At least one task block is present.

## Success Signals (Required)

1. A plan file is written under `docs/plans/`.
2. Each task has `Files`, `Steps`, `Verification`, `Dependencies`, and `Output`.
3. Verification commands are executable and include expected signals.
4. Output schema is returned with evidence.

## Blocked State Rules

Enter `BLOCKED` only when:
- Required requirements/design context is unavailable.
- Critical file paths cannot be validated.
- A required verification command cannot be executed in the current turn.

When `STATUS=BLOCKED`:
- `FILES_WRITTEN` should be `"none"` unless partial output was explicitly requested.
- `BLOCK_REASON` must describe the concrete blocker.
- `UNBLOCK_ACTION` must provide one clear next action.

## Execution Handoff (No Hard Dependency)

After saving the plan, offer execution paths:

1. Execute now in the current session.
2. Execute in the current session using `subagent-driven-development`.
3. Execute in a separate session using `executing-plans`.

If a path is unavailable in the environment, state that and continue with the nearest available option.

## Common Mistakes

- Vague tasks with no verifiable command.
- Missing or guessed file paths.
- Overly large steps that hide dependency risk.
- Excessive boilerplate code blocks that inflate context without improving execution quality.
- Forcing commit steps when the user did not request commit-level planning.

## Enforcement Rules

- Use this skill only for implementation planning, not requirements/design authoring.
- Keep trigger boundary with `writing-specs` strict to avoid routing ambiguity.
- Do not return suggestion-only output; produce or update the actual plan file.
