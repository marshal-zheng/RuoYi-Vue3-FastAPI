---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification
---

# Using Git Worktrees

Git worktrees create isolated workspaces sharing the same repository, allowing work on multiple branches simultaneously without switching.

**Core principle:** Systematic directory selection + safety verification = reliable isolation.

**Announce at start:** "正在使用 using-git-worktrees skill 来设置隔离工作区。"

## Directory Selection (Priority Order)

1. **Check existing directories:**
   ```bash
   ls -d .worktrees 2>/dev/null     # Preferred (hidden)
   ls -d worktrees 2>/dev/null      # Alternative
   ```
   If both exist, `.worktrees` wins.

2. **Check AGENTS.md** for worktree directory preference.

3. **Ask user** if no directory exists and no preference found:
   - `.worktrees/` (project-local, hidden)
   - `~/.worktrees/<project-name>/` (global location)

## Safety Verification

For project-local directories, **MUST verify ignored before creating:**

```bash
git check-ignore -q .worktrees 2>/dev/null
```

If NOT ignored → add to `.gitignore` → commit → proceed.

Global directory needs no verification.

## Creation Steps

```bash
# 1. Detect project name
project=$(basename "$(git rev-parse --show-toplevel)")

# 2. Create worktree with new branch
git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"

# 3. Run project setup (auto-detect)
[ -f package.json ] && npm install
[ -f requirements.txt ] && pip install -r requirements.txt
[ -f Cargo.toml ] && cargo build
[ -f go.mod ] && go mod download

# 4. Verify clean baseline
# Run project-appropriate test command
```

If tests fail → report failures, ask whether to proceed.

If tests pass → report ready:
```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check AGENTS.md → Ask user |
| Directory not ignored | Add to .gitignore + commit |
| Tests fail during baseline | Report failures + ask |

## Integration

**Called by:**
- `brainstorming` — when implementation follows
- `subagent-driven-development` / `executing-plans` — before executing tasks

**Pairs with:**
- `finishing-a-development-branch` — cleanup after work complete
