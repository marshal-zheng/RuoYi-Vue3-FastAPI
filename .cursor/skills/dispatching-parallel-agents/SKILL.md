---
name: dispatching-parallel-agents
description: Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies
---

# Dispatching Parallel Agents

When you have multiple unrelated failures or tasks, investigating them sequentially wastes time. Each independent problem can be solved in parallel.

**Core principle:** Dispatch one agent per independent problem domain. Let them work concurrently.

## When to Use

**Use when:**
- 3+ test files failing with different root causes
- Multiple subsystems broken independently
- Each problem can be understood without context from others
- No shared state between investigations

**Don't use when:**
- Failures are related (fix one might fix others)
- Need to understand full system state
- Agents would interfere with each other (editing same files)

## The Pattern

### 1. Identify Independent Domains

Group failures by what's broken. Each domain is independent — fixing one doesn't affect others.

### 2. Create Focused Agent Tasks

Each agent gets:
- **Specific scope:** one test file or subsystem
- **Clear goal:** make these tests pass
- **Constraints:** don't change other code
- **Expected output:** summary of what you found and fixed

### 3. Dispatch in Parallel

```
Task("Fix agent-tool-abort.test.ts failures")
Task("Fix batch-completion-behavior.test.ts failures")
Task("Fix tool-approval-race-conditions.test.ts failures")
// All three run concurrently
```

### 4. Review and Integrate

When agents return:
- Read each summary
- Verify fixes don't conflict
- Run full test suite
- Integrate all changes

## Agent Prompt Best Practices

| Quality | Good | Bad |
|---------|------|-----|
| Scope | "Fix agent-tool-abort.test.ts" | "Fix all the tests" |
| Context | Paste error messages and test names | "Fix the race condition" |
| Constraints | "Do NOT change production code" | No constraints |
| Output | "Return summary of root cause and changes" | "Fix it" |

## Verification

After agents return:
1. Review each summary — understand what changed
2. Check for conflicts — did agents edit same code?
3. Run full suite — verify all fixes work together
4. Spot check — agents can make systematic errors
