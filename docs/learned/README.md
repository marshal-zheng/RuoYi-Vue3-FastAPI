# Reusable Patterns

Patterns and solutions extracted from problem-solving sessions during development.

## Purpose

This directory captures:
- **Error Resolution Patterns** - Root causes and fixes for non-trivial errors
- **Debugging Techniques** - Effective tool combinations and diagnostic approaches
- **Workarounds** - Library quirks, API limitations, version-specific fixes
- **Project Conventions** - Discovered codebase patterns and architectural decisions

## Format

Each pattern is documented in a standalone markdown file:

```markdown
# [Descriptive Pattern Name]

**Extracted:** 2026-02-10
**Context:** When this pattern applies

## Problem
What problem this solves - be specific

## Solution
The pattern/technique/workaround

## Example
Code example if applicable

## When to Use
Trigger conditions for applying this pattern
```

## Creation

Use `.cursor/commands/learn.md` to extract patterns from current sessions.

## Guidelines

**DO extract:**
- Patterns that will save time in future sessions
- Non-obvious debugging approaches
- Framework-specific workarounds
- Architectural decisions with rationale

**DON'T extract:**
- Trivial fixes (typos, simple syntax errors)
- One-off issues (specific API outages)
- Common knowledge (basic Python/TypeScript patterns)
- Obvious solutions

## Examples

Good patterns:
- `vxe-table-object-display-issue.md` - Handling v-model with object values
- `alembic-async-engine-setup.md` - Configuring async SQLAlchemy with Alembic
- `pinia-store-typescript-typing.md` - Proper typing for Pinia stores

Not worth extracting:
- `fixed-import-typo.md`
- `updated-package-version.md`
