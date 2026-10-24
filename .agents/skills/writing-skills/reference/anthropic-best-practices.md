# Skill Authoring Best Practices (Cursor-Compatible)

Use this guide when writing or refining Skills for Cursor-style agent workflows.

The goal is simple: make Skills easy to discover, easy to execute, and hard to misuse.

## Core principles

### Be concise

Your Skill competes for context with:

- system instructions
- user request and conversation history
- other loaded skill content

Keep only information that improves outcomes. Remove explanatory filler.

Good:

````markdown
## Extract PDF text

Use pdfplumber:

```python
import pdfplumber

with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
````

Bad:

```markdown
## Extract PDF text

PDF files are a common format. There are many libraries for PDF parsing. You should install one and then run code to parse the pages...
```

### Set the right degree of freedom

Use higher freedom when multiple approaches are safe. Use lower freedom when mistakes are expensive.

- High freedom: code review heuristics, analysis workflows
- Medium freedom: templates with a few parameters
- Low freedom: fragile migrations, destructive operations, strict release steps

### Test across model tiers you actually use

If your team uses multiple model tiers (for example fast, balanced, reasoning-heavy), test all of them.

What works on a high-reasoning model may be under-specified for a fast model.

## Skill structure

### Frontmatter

`SKILL.md` frontmatter should contain only:

- `name` (letters, numbers, hyphens; max 64 chars)
- `description` (single line; max 1024 chars)

Example:

```yaml
---
name: writing-skills
description: Use when creating new skills, editing existing skills, or verifying skills before deployment.
---
```

### Naming conventions

Prefer clear, activity-oriented names.

Good:

- `writing-skills`
- `test-driven-development`
- `verification-before-completion`

Avoid:

- `helper`
- `utils`
- `misc-tools`

### Writing effective descriptions

`description` drives discovery. Keep it focused on triggering conditions.

Rule:

- Describe when to use the Skill
- Do not summarize full workflow details
- Use third-person wording

Good:

```yaml
description: Use when implementing any feature or bugfix, before writing implementation code.
```

Bad:

```yaml
description: Use this skill to write tests first, run them, implement code, then refactor and verify.
```

### Progressive disclosure

Keep `SKILL.md` as an overview and link to deeper files only when needed.

Pattern:

```text
my-skill/
├── SKILL.md
├── reference.md
├── examples.md
└── scripts/
    └── validate.py
```

In `SKILL.md`, link directly to optional files:

```markdown
- Advanced reference: `reference.md`
- Examples: `examples.md`
- Validator script: `scripts/validate.py`
```

### Keep references one level deep

Avoid chained references (`SKILL.md -> advanced.md -> details.md`).

Preferred:

- `SKILL.md` links directly to every important file.

### Add a table of contents to long reference files

If a reference file is longer than ~100 lines, include a short TOC at the top.

## Workflow and feedback loops

### Use explicit workflows for multi-step tasks

For complex tasks, include a checklist and deterministic sequence.

Example:

```text
Task Progress:
- [ ] Step 1: Analyze input
- [ ] Step 2: Build plan artifact
- [ ] Step 3: Validate plan
- [ ] Step 4: Execute
- [ ] Step 5: Verify output
```

### Add validation loops

For quality-critical tasks, require a loop:

1. run validator
2. fix issues
3. rerun validator
4. continue only when clean

## Content guidelines

### Avoid time-sensitive instructions in the main path

Do not write temporary instructions like "before August" in the main workflow.

Use an `Old patterns` section for deprecated approaches.

### Use consistent terminology

Pick one term per concept and stick to it.

Examples:

- always `field` (not field/box/element mixed)
- always `API endpoint` (not endpoint/route/url mixed)

### Prefer a default plus an escape hatch

Do not list five equivalent options without guidance.

Preferred style:

```markdown
Use `pdfplumber` for PDF text extraction by default.
For scanned PDFs, switch to OCR (`pdf2image` + `pytesseract`).
```

## Scripts and runtime guidance

### Solve problems in scripts, do not punt

If you provide scripts, handle expected failures clearly.

Good:

```python
def process_file(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return ""
```

Bad:

```python
def process_file(path):
    return open(path).read()
```

### Document constants

Avoid unexplained magic numbers.

Good:

```python
REQUEST_TIMEOUT = 30  # seconds: balances latency and reliability
MAX_RETRIES = 3       # most transient failures resolve within 2-3 attempts
```

### Prefer executable utility scripts for deterministic operations

If an operation is repeatable and strict, provide a script and tell the agent to run it.

Example:

```markdown
Run `python scripts/validate_fields.py fields.json` before writing output files.
```

### Use plan-validate-execute for risky changes

For batch edits or destructive operations:

1. generate plan artifact (for example `changes.json`)
2. validate artifact
3. execute only if validation passes
4. verify final result

### Be explicit about dependencies

Never assume tools are preinstalled. State required packages and commands.

Example:

```markdown
Install dependencies first:
`pip install pypdf`
```

### Use fully qualified MCP tool names

Use `ServerName:tool_name` format.

Example:

- `BigQuery:bigquery_schema`
- `GitHub:create_issue`

## Evaluation and iteration

### Build evaluations before writing large docs

Start with representative scenarios and baseline behavior without the Skill.

Suggested minimum:

- 3 scenarios
- explicit expected behaviors
- same scenarios rerun after updates

### Iterate from real usage

Loop:

1. run real task with current Skill
2. observe misses/confusion
3. refine wording/structure
4. rerun scenario

### Observe how the agent navigates files

Look for:

- ignored files (not discoverable enough)
- repeated reads of one section (may belong in `SKILL.md`)
- missed links (link text too weak)

## Technical notes

- Use forward slashes in paths: `scripts/validate.py`
- Keep `SKILL.md` body under 500 lines
- Move heavy reference and examples to separate files
- Keep prose plain Markdown (no MDX-only components)

## Checklist for effective Skills

### Core quality

- [ ] `description` is specific and searchable
- [ ] `description` describes triggering conditions (when to use)
- [ ] `SKILL.md` is concise and under 500 lines
- [ ] references are one level deep from `SKILL.md`
- [ ] terminology is consistent
- [ ] examples are concrete and reusable

### Code and scripts

- [ ] scripts include error handling
- [ ] constants are justified
- [ ] required dependencies are declared
- [ ] verification steps exist for risky operations
- [ ] script execution intent is explicit

### Testing

- [ ] baseline behavior captured before major edits
- [ ] at least three evaluation scenarios
- [ ] rerun evaluations after each important change
- [ ] tested with the model tiers used by your team

## Quick compatibility guardrail

Before committing a skill file, quickly check for non-portable markup and platform-specific leftovers:

```bash
rg -n "<Note>|<Warning>|<Tip>|<Card|<CardGroup|theme=\\{null\\}|/en/docs|/en/api|mintcdn" .cursor/skills/<skill-name>/
```

Expected result: no matches, unless you intentionally keep those patterns.
