---
name: update-codemaps
description: Use when architecture changes are stable enough to document (for release, handoff, onboarding, or refactor planning) and docs/codemaps need a refresh, or when the user explicitly requests a codemap refresh.
---

# Update Codemaps (Execution Contract)

Refresh architecture snapshots in `docs/codemaps/` from the current repository structure.

**Announce at start:** "I'm using the update-codemaps skill to refresh architecture codemaps."
**Language:** Generated codemap file content must be in Chinese.

## When to Use

- After architecture-level changes (new modules, layer moves, major routing/data-flow changes)
- Before onboarding or large refactor planning
- Periodic maintenance for active repositories
- When user explicitly asks to refresh codemaps

## When NOT to Use

- Minor file edits that don't change architecture
- Only content/logic changes within existing files
- Documentation-only updates unrelated to architecture

## Output File Set (Adaptive)

Do not assume any predefined codemap file names or categories.
Derive the codemap file set entirely from the current repository topology.

Scope communication rule:
- Before writing files, provide a short topology summary and a concrete proposed codemap file list.
- Always ask user confirmation for the proposed file list before first write in this run.
- If an existing codemap set already exists, ask again when file scope changes (add/remove/rename).
- Do not generate codemap files until scope confirmation is received.

## Required Tool Actions (Must Execute)

1. Read existing codemap files and repository structure.
2. Assess repository topology from the current codebase layout and deployable boundaries.
3. Propose an adaptive codemap file set and communicate it to the user for confirmation.
4. Scan relevant directories using `rg`, `find`, or equivalent tools.
5. Generate codemap drafts for approved map files.
6. Compute deterministic change ratio per file.
7. Apply approval gates for large diffs and map-scope changes.
8. Write approved files and `docs/codemaps/.diff-report.txt`.
9. Return the required output schema with evidence and next action.

## Topology Assessment (Discovered, Not Hardcoded)

Rules:
- Discover architectural units from the live tree (apps, services, packages, deployable components, and shared layers).
- Build map file candidates from discovered units, not from templates.
- Use repository-relative paths under `docs/codemaps/` for every proposed file.
- If an optional path does not exist, continue without failure and note it in evidence.
- Do not hardcode business module names; discover from current tree state.
- In multi-service architectures, propose one codemap per independently deployable service/component.

## Parallelization Rule

- If parallel/subagent execution is available, run one scan per selected map file (cap at 6 in parallel).
- If unavailable, run the same workflow serially.
- Output format and approval behavior must remain identical in both modes.

## Diff and Approval Rule (Deterministic)

For each output file:

1. If no previous file exists: require scope confirmation first, then write (first generation).
2. If previous file exists:
  - Compare old/new content excluding line 1 timestamp (`<!-- Updated: YYYY-MM-DD -->`).
  - `changed_lines = added_lines + removed_lines` (line-level diff).
  - `baseline_lines = max(previous_lines_without_timestamp, 1)`.
  - `change_ratio = changed_lines / baseline_lines`.
3. If `change_ratio <= 0.30`: overwrite directly.
4. If `change_ratio > 0.30`: do not overwrite; request user approval with summary first.
5. If map file set is added/removed/renamed vs existing codemap set: request approval before writing.

## Output Schema (Required Every Turn)

Use this exact structure:

```markdown
STATUS: <one of: SCOPING | CODEMAPS_UPDATED | WAITING_APPROVAL | BLOCKED>
TOPOLOGY_SUMMARY: <1-3 lines>
PROPOSED_MAPS:
- <path | purpose>
FILES_WRITTEN:
- <path or "none">
PENDING_APPROVAL:
- <path | change_ratio | short summary>
EVIDENCE:
- READ: <files inspected>
- SEARCH: <queries and key hits>
- COMMAND: <commands run and pass/fail>
NEXT_ACTION: <single concrete next action>
GATE_MESSAGE: <scope/diff approval request text or "none">
BLOCK_REASON: <required when STATUS=BLOCKED, otherwise "none">
UNBLOCK_ACTION: <required when STATUS=BLOCKED, otherwise "none">
```

## Codemap Template

Each codemap file follows this structure:

```markdown
<!-- Updated: YYYY-MM-DD -->
# [Map Title]

> One-line architecture summary.

## [Module/Section Name]

**Purpose:** One-line description.

**Key files:**
- `path/to/entry.py` — entry point / main purpose
- `path/to/important.py` — why it matters

**Dependencies:** Lists internal cross-module deps.

**Patterns:** Architectural patterns in use (e.g., repository pattern, Pinia stores).

## [Next Module/Section]
...
```

## Rules

1. **High-level only** — no function signatures, no implementation details
2. **Under 200 lines** per file — be concise, prioritize important modules
3. **Freshness timestamp** — `<!-- Updated: YYYY-MM-DD -->` at line 1 of every file
4. **Key files only** — entry points and architecturally significant files, not exhaustive listings
5. **Dependencies = internal** — cross-module dependencies within this repo, not pip/npm packages
6. **Patterns = observable** — only document patterns actually in use, not aspirational
7. **Chinese output** — all natural-language text in codemap files must be Chinese (keep file paths and code identifiers unchanged)

## Minimum Verification Commands (Required)

Use `<selected_maps>` as the user-approved list of codemap files (space-separated paths):

- `test -d docs/codemaps`
- `for f in <selected_maps>; do test -f "$f"; done`
- `for f in <selected_maps>; do head -n1 "$f" | rg '^<!-- Updated: [0-9]{4}-[0-9]{2}-[0-9]{2} -->$'; done`
- `for f in <selected_maps>; do test "$(wc -l < "$f")" -le 200; done`
- `test -f docs/codemaps/.diff-report.txt`

Pass criteria:
- All commands succeed.
- No pending approvals remain when `STATUS=CODEMAPS_UPDATED`.
- Verified file set matches the approved `PROPOSED_MAPS`.

## Success Signals (Required)

1. Approved map scope is documented and applied.
2. Every selected codemap file exists and is updated.
3. Every selected file has a valid freshness timestamp on line 1.
4. Every selected file stays within 200 lines.
5. `.diff-report.txt` exists and summarizes per-file changes.
6. Output schema is returned with concrete evidence.

## Blocked State Rules

Enter `BLOCKED` only when:
- Required scan roots are inaccessible.
- Essential commands fail and cannot be resolved in this turn.
- Approval is required but cannot be requested due channel/tool constraints.

When `STATUS=BLOCKED`:
- `FILES_WRITTEN` should be `"none"` unless partial output was explicitly requested.
- Provide concrete `BLOCK_REASON` and one actionable `UNBLOCK_ACTION`.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Listing every file | Focus on entry points and key files only |
| Including function signatures | Stay at module/file level |
| Exceeding 200 lines | Cut less important sections, merge small modules |
| Missing freshness date | Always add `<!-- Updated: YYYY-MM-DD -->` on line 1 |
| Skipping deterministic diff rule | Always compute change ratio before overwrite |
| Hardcoding module names | Discover modules from current tree state |
| Failing on optional missing paths | Continue scan and note missing path in evidence |
| Mixing English prose into codemap files | Keep all narrative text in Chinese; preserve paths/identifiers as-is |
