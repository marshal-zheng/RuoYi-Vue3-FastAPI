---
name: writing-skills
description: Use when creating new skills, editing existing skills, or verifying skills work before deployment
---

# Writing Skills

## Overview

Skills are reusable reference guides for techniques, patterns, or tools. They help future agent instances find and apply effective approaches.

**Skills are:** Reusable techniques, patterns, tools, reference guides.
**Skills are NOT:** Narratives about how you solved a problem once.

## Skill Types

- **Technique** — concrete method with steps (condition-based-waiting, root-cause-tracing)
- **Pattern** — way of thinking about problems (flatten-with-flags)
- **Reference** — API docs, syntax guides, tool documentation

## Directory Structure

```
skills/
  skill-name/
    SKILL.md              # Main reference (required)
    reference/            # Optional deep guidance and long docs
    examples/             # Optional worked examples
    scripts/              # Optional executable helpers
```

Personal skills: `~/.cursor/skills/`
Project skills: `.cursor/skills/`

## SKILL.md Structure

**Frontmatter (YAML):**
- `name`: letters, numbers, hyphens only (max 64 chars)
- `description`: third-person, starts with "Use when...", describes triggering conditions ONLY (NOT workflow)

```markdown
---
name: skill-name
description: Use when [specific triggering conditions]
---

# Skill Name

## Overview
Core principle in 1-2 sentences.

## When to Use
Symptoms and use cases. When NOT to use.

## Core Pattern
Before/after code comparison.

## Quick Reference
Table or bullets for scanning.

## Common Mistakes
What goes wrong + fixes.
```

## Description Best Practices

**CRITICAL: Description = When to Use, NOT What the Skill Does.**

```yaml
# ❌ BAD: Summarizes workflow — agent may follow description instead of reading skill
description: Use for TDD - write test first, watch it fail, write minimal code, refactor

# ✅ GOOD: Just triggering conditions
description: Use when implementing any feature or bugfix, before writing implementation code
```

## Token Efficiency

- Target: main SKILL.md under 500 lines
- Move heavy reference (100+ lines) to separate files
- Use cross-references instead of repeating content
- One excellent example beats many mediocre ones

## Supplemental Files

Use these only when needed:
- `reference/anthropic-best-practices.md` for broader authoring and structure guidance
- `reference/testing-skills-with-subagents.md` for pressure testing and loophole-closing workflow
- `reference/persuasion-principles.md` for pressure-design rationale
- `reference/graphviz-conventions.dot` for `dot` diagram style conventions
- `examples/SKILL_MD_TESTING.md` for a full worked testing campaign example
- `scripts/render-graphs.js` to render `dot` blocks in a `SKILL.md` into SVG files

## Cross-Referencing Other Skills

Use skill name only:
- ✅ `Use test-driven-development skill`
- ❌ `@skills/test-driven-development/SKILL.md` (force-loads, burns context)

## When to Create

**Create when:** technique wasn't intuitive, broadly applicable, reusable across projects.

**Don't create for:** one-off solutions, standard practices, project-specific conventions (put in AGENTS.md).

## Skill Creation Checklist

- [ ] Name uses only letters, numbers, hyphens
- [ ] YAML frontmatter with name and description
- [ ] Description starts with "Use when..." (triggering conditions only)
- [ ] Keywords throughout for search
- [ ] Clear overview with core principle
- [ ] Code inline OR link to separate file
- [ ] One excellent example
- [ ] Under 500 lines

## Anti-Patterns

- **Narrative storytelling** — "In session X, we found..." → extract the technique
- **Multi-language examples** — one great example is enough
- **Vague labels** — use semantic names (not helper1, step2)
- **Verbose descriptions** — keep descriptions about when, not how

See `reference/anthropic-best-practices.md` for additional guidance.
