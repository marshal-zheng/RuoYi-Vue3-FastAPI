---
name: receiving-code-review
description: Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation
---

# Code Review Reception

Code review requires technical evaluation, not emotional performance.

**Core principle:** Verify before implementing. Ask before assuming. Technical correctness over social comfort.

## The Response Pattern

```
WHEN receiving code review feedback:

1. READ: Complete feedback without reacting
2. UNDERSTAND: Restate requirement in own words (or ask)
3. VERIFY: Check against codebase reality
4. EVALUATE: Technically sound for THIS codebase?
5. RESPOND: Technical acknowledgment or reasoned pushback
6. IMPLEMENT: One item at a time, test each
```

## Handling Unclear Feedback

If any item is unclear → STOP, do not implement anything yet. Ask for clarification on unclear items.

Items may be related. Partial understanding = wrong implementation.

```
User: "Fix items 1-6"
You understand 1,2,3,6. Unclear on 4,5.

❌ WRONG: Implement 1,2,3,6 now, ask about 4,5 later
✅ RIGHT: "I understand 1,2,3,6. Need clarification on 4 and 5 before proceeding."
```

## Source-Specific Handling

### From User
- Trusted — implement after understanding
- Still ask if scope unclear
- Skip to action or technical acknowledgment

### From External Reviewers
Before implementing:
1. Technically correct for THIS codebase?
2. Breaks existing functionality?
3. Reason for current implementation?
4. Works on all platforms/versions?
5. Does reviewer understand full context?

If suggestion seems wrong → push back with technical reasoning.

If conflicts with user's prior decisions → stop and discuss with user first.

## YAGNI Check

If reviewer suggests "implementing properly":
- grep codebase for actual usage
- If unused: "This isn't called. Remove it (YAGNI)?"
- If used: Then implement properly

## Implementation Order

For multi-item feedback:
1. Clarify anything unclear FIRST
2. Implement in order: blocking → simple fixes → complex fixes
3. Test each fix individually
4. Verify no regressions

## When to Push Back

Push back when:
- Suggestion breaks existing functionality
- Reviewer lacks full context
- Violates YAGNI (unused feature)
- Technically incorrect for this stack
- Conflicts with user's architectural decisions

How: use technical reasoning, reference working tests/code.

## Acknowledging Correct Feedback

```
✅ "Fixed. [Brief description of what changed]"
✅ "Good catch - [specific issue]. Fixed in [location]."
✅ [Just fix it and show in the code]
```

Actions speak. Just fix it. The code itself shows you heard the feedback.

## GitHub Thread Replies

When replying to inline review comments on GitHub, reply in the comment thread (`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`), not as a top-level PR comment.
