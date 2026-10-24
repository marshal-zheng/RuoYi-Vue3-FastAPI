---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks in the current session
---

# Subagent-Driven Development

Execute spec by dispatching fresh subagent per task, with two-stage review after each: spec compliance first, then code quality.

**Core principle:** Fresh subagent per task + two-stage review = high quality, fast iteration.

## When to Use

- Have a `tasks.md` from spec and tasks are mostly independent
- Want to stay in this session (vs. `executing-plans` for separate session)

## The Process

### Per Task Loop:

1. **Dispatch implementer subagent** (`./implementer-prompt.md`)
   - If subagent asks questions → answer, then let them proceed
   - Subagent implements, tests, commits, self-reviews
2. **Dispatch spec reviewer** (`./spec-reviewer-prompt.md`)
   - If issues found → implementer fixes → re-review
3. **Dispatch code quality reviewer** (`./code-quality-reviewer-prompt.md`)
   - If issues found → implementer fixes → re-review
4. **Mark task complete** in TodoWrite and `tasks.md`
5. Repeat for next task

### After All Tasks:

- Dispatch final code-reviewer for entire implementation
- Use `finishing-a-development-branch` skill to complete

## Prompt Templates

- `./implementer-prompt.md` — implementer subagent
- `./spec-reviewer-prompt.md` — spec compliance reviewer
- `./code-quality-reviewer-prompt.md` — code quality reviewer

## Key Rules

**Never:**
- Skip reviews (spec compliance OR code quality)
- Start code quality review before spec compliance is approved
- Dispatch multiple implementation subagents in parallel (conflicts)
- Move to next task while either review has open issues
- Start on main/master without explicit user consent

**If subagent asks questions:** answer clearly before letting them proceed.

**If reviewer finds issues:** implementer fixes → reviewer re-reviews → repeat until approved.

## Integration

**Related skills:**
- `writing-specs` — creates the specs this skill executes
- `using-git-worktrees` — set up isolated workspace before starting
- `requesting-code-review` — code review template for reviewer subagents
- `finishing-a-development-branch` — complete development after all tasks
- `test-driven-development` — subagents follow TDD for each task
- `executing-plans` — alternative: separate session execution
