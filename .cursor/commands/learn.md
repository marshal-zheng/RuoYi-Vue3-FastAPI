# /learn - Extract Reusable Patterns

Analyze the current session and extract any patterns worth saving.

## When to Trigger

Run `/learn` at any point during a session when you've solved a non-trivial problem.

## What to Extract

Look for:

1. **Error Resolution Patterns**
   * What error occurred?
   * What was the root cause?
   * What approach fixed it?
   * Is this reusable for similar errors?

2. **Debugging Techniques**
   * Non-obvious debugging steps
   * Effective tool combinations
   * Diagnostic patterns

3. **Workarounds**
   * Library quirks
   * API limitations
   * Version-specific fixes

4. **Project-Specific Patterns**
   * Codebase conventions discovered
   * Architectural decisions made
   * Integration patterns

## Output Format

Create a document at `docs/learned/[pattern-name].md`:

```markdown
# [Descriptive Pattern Name]

**Extracted:** [Date]
**Context:** [Brief description of when this applies]

## Problem
[What problem this solves - be specific]

## Solution
[The pattern/technique/workaround]

## Example
[Code example if applicable]

## When to Use
[Trigger conditions - what should activate this skill]
```

## Workflow

1. Review the session for extractable patterns
2. Identify the most valuable/reusable insights
3. Draft the document
4. Ask the user to confirm before saving
5. Save to `docs/learned/`

## Guidelines

* Do not extract trivial fixes (typos, simple syntax errors)
* Do not extract one-off issues (specific API outages, etc.)
* Focus on patterns that will save time in future sessions
* Keep each document focused - one pattern per file
