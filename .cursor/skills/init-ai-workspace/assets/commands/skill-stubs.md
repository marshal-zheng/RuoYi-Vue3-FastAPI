# Skill Stubs

Minimal functional SKILL.md templates for workspace initialization. Each section is one complete SKILL.md file content.

Copy each stub into `.cursor/skills/<name>/SKILL.md`. Skip if file already exists.

---

## brainstorming

```markdown
---
name: brainstorming
description: Use when the user wants to brainstorm, compare approaches, explore architecture or tech choices, or refine unclear requirements before implementation.
---

# Brainstorming Ideas Into Designs

Turn ideas into validated designs through collaborative dialogue.

## Workflow

1. **Understand** — Check project state, ask one question per message, prefer multiple choice
2. **Explore** — Propose 2-3 approaches with trade-offs, lead with recommendation
3. **Hand Off** — Once aligned, offer to generate spec with `writing-specs` skill

## Rules

- One question per message — never batch multiple questions
- Challenge scope ruthlessly (YAGNI) — strip unnecessary features
- If multiple requests, force convergence: ask which is the priority for this round
- Propose 2-3 approaches before settling — never jump to implementation
- All dialogue in Chinese
```

---

## skill-loader

```markdown
---
name: skill-loader
description: Use when starting a conversation to identify and load applicable skills before any response or action.
---

# Skill Loader

Ensure relevant skills are loaded and followed before any response.

## Required Actions

1. Inspect available skill names and descriptions
2. Match user request to skill trigger conditions
3. Load each applicable skill
4. Announce: "Using <skill-name> to <purpose>"
5. Follow loaded skills exactly

## The Rule

Load relevant skills BEFORE any response or action. If a loaded skill is non-applicable, state that briefly and continue.

## Skill Priority

1. **Process skills first** (brainstorming, debugging) — determine approach
2. **Implementation skills second** (frontend/backend conventions) — guide execution
3. **Quality gates before completion** (verification, code review)

## Red Flags — STOP if you think:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "The skill is overkill" | Simple things become complex. Use it. |
```

---

## update-codemaps

```markdown
---
name: update-codemaps
description: Use when architecture changes are stable enough to document, docs/codemaps need a refresh, or the user explicitly requests a codemap update.
---

# Update Codemaps

Scan project structure and refresh architecture documentation in `docs/codemaps/`.

## Workflow

1. Scan project modules and directory structure
2. Generate/update codemap files under `docs/codemaps/`
3. Compute diff against previous version
4. If changes > 30%, ask user for approval before overwriting
5. Write diff summary to `docs/codemaps/.diff-report.txt`

## What to Capture

For each module:
- **Purpose** — one-line description
- **Key files** — entry points and important files only
- **Dependencies** — internal cross-module references
- **Patterns** — architectural patterns in use

## Rules

- Focus on high-level structure, not implementation details
- Add `Updated: YYYY-MM-DD` timestamp at top of each file
- Keep each file under 200 lines
- Adjust codemap files to match actual project structure
```

---

## writing-plans

```markdown
---
name: writing-plans
description: Use when the task is medium-complexity and already scoped, and the user needs a lightweight execution plan before coding without creating a formal multi-file spec package.
---

# Writing Plans

Generate a single implementation plan document in `docs/plans/`.

## When to Use

- Requirements/design already clear
- Multiple dependent steps benefit from explicit ordering
- NOT for discovery (use `brainstorming`) or formal specs (use `writing-specs`)

## Plan Location

`docs/plans/YYYY-MM-DD-<feature-name>.md`

## Required Structure

Each plan must include:

- **Goal** — single-sentence outcome
- **Inputs** — approved specs/design links
- **Task List** — ordered tasks, each with:
  - Files (create/modify/test)
  - Steps (single actions)
  - Verification (exact commands + expected output)
  - Dependencies (task IDs or "none")
  - Output (concrete artifact)

## Rules

- Use dependency order — no forward references
- Each step: one action, 2-10 minutes
- Include exact verification commands
- Do not force commits unless user requests
```

---

## writing-skills

```markdown
---
name: writing-skills
description: Use when creating new skills, editing existing skills, or verifying skills work before deployment.
---

# Writing Skills

Skills are reusable reference guides for techniques, patterns, or tools.

## SKILL.md Structure

Frontmatter: `name` (letters/numbers/hyphens, max 64) + `description` (starts with "Use when...")

Sections: Overview → When to Use → Core Pattern → Quick Reference → Common Mistakes

## Key Rules

- Description = triggering conditions only, NOT workflow summary
- SKILL.md under 500 lines
- Move heavy reference (100+ lines) to separate files in `reference/`
- Keep references one level deep from SKILL.md
- One excellent example beats many mediocre ones
- Use consistent terminology throughout

## Anti-Patterns

- Narrative storytelling ("In session X, we found...")
- Vague names (helper, utils, tools)
- Verbose descriptions that summarize the full workflow
- Multi-level reference chains (SKILL → A.md → B.md)
```

---

## writing-specs

```markdown
---
name: writing-specs
description: Use when the user needs a formal feature specification package before implementation, or when an existing spec package must be resumed or updated.
---

# Writing Specs

Generate a three-file spec package with phase gates.

## Spec Location

`docs/specs/<feature-name>/` with: `requirements.md`, `design.md`, `tasks.md`

## Three Phases (Strict Order)

1. **Requirements** (`requirements.md`)
   - User stories with EARS acceptance criteria
   - IDs: `R<N>`, acceptance criteria: `R<N>.AC<N>`
   - Gate: explicit user approval before proceeding

2. **Design** (`design.md`)
   - Architecture, data flow (Mermaid), API contracts, data models, security, test strategy
   - Must reference real project context from code search
   - Gate: explicit user approval before proceeding

3. **Tasks** (`tasks.md`)
   - Implementation tasks in dependency order
   - Each task maps to AC IDs via `_需求追溯: R#.AC#_`
   - All AC IDs must exist in requirements.md

## Rules

- Never skip phase order
- Never proceed without explicit approval
- Resume from first incomplete phase if folder exists
- Keep generated content in Chinese (IDs and code identifiers unchanged)
```

---

## frontend-conventions (optional)

```markdown
---
name: frontend-conventions
description: Use when creating or modifying frontend files, including views, components, API modules, store modules, and styles.
---

# Frontend Conventions

Project-local frontend development standards.

## Setup

**Customize this skill for your project.** Replace placeholders with actual patterns.

## Sections to Define

- **Tech stack** — framework, build tool, UI library, state management
- **Directory structure** — where views, components, API modules, stores live
- **Component patterns** — naming, props, slots, composition API conventions
- **API layer** — request/response patterns, error handling
- **Styling** — CSS approach, theme variables, responsive breakpoints
- **Testing** — test framework, coverage thresholds, test file naming

## Rules

- Follow existing project patterns before introducing new abstractions
- Check actual codebase before assuming conventions
```

---

## backend-conventions (optional)

```markdown
---
name: backend-conventions
description: Use when creating or modifying backend files, including controllers, services, repositories, entities, config, middleware, and tests.
---

# Backend Conventions

Project-local backend development standards.

## Setup

**Customize this skill for your project.** Replace placeholders with actual patterns.

## Sections to Define

- **Tech stack** — framework, ORM, database, auth approach
- **Layering** — controller → service → repository (or your pattern)
- **Directory structure** — where each layer lives
- **Entity/model patterns** — DO, VO, DTO conventions
- **Error handling** — error codes, response format
- **Testing** — test framework, fixtures, markers, coverage

## Rules

- Follow existing project patterns before introducing new abstractions
- Check actual codebase before assuming conventions
```
