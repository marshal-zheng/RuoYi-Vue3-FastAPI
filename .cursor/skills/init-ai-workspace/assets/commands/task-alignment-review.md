# /task-alignment-review — Spec Alignment Review (agent-optimized)

Goal: Using only the Spec + current codebase + real verification outputs, review **item-by-item** whether the implementation is **100% aligned** with the Spec.
Scope: Review + report only. **Do not modify code** unless the user explicitly asks.

## Spec selection (priority)
- If the user provides a spec path/file(s): **use exactly that** (no guessing).
- Otherwise: list first-level directories under `docs/specs/` and ask the user to choose `<feature>`.

## Required actions (do in this order)
1) **Read the Spec fully (no skipping):**
   - `docs/specs/<feature>/requirements.md`
   - `docs/specs/<feature>/design.md`
   - `docs/specs/<feature>/tasks.md`

2) **Build a Spec Checklist (output this first, before judging alignment):**
   - Break the Spec into minimal, testable items: `R1..`, `D1..`, `T1..`
   - Each item must be a single verifiable requirement/constraint/acceptance point
   - Keep items short; preserve MUST/SHOULD/forbidden, thresholds, edge cases, compatibility, error handling

3) **Collect evidence for each checklist item (Spec → touchpoints → code):**
   - Derive concrete touchpoints from the Spec (module names, routes, APIs, configs, tables, error codes, feature flags, test names)
   - Use repo-wide search to locate relevant code and read the critical paths
   - Evidence format must be: `path/to/file:Ln-Lm` + one-sentence summary
   - If not found: mark ❌ and record what you searched (keywords + scope) and that it did not match

   Evidence priority (use the strongest available):
   - Verification output > tests > entrypoints/handlers > core logic > helpers

4) **Run verification steps (must actually execute and paste raw outputs):**
   - Run commands explicitly specified in the Spec first
   - If the Spec does not specify commands: infer the closest standard set from the project (tests/lint/typecheck/build)
   - If you cannot run something: state why (missing deps/env/etc). **Do not assume pass**

## Status rubric (single standard)
- ✅ Aligned: fully implemented and consistent; has code or output evidence
- ⚠️ Partial/Deviates: incomplete coverage, missing edge cases/non-functional constraints, or plausible deviation; must explain reason + impact
- ❌ Not aligned: not implemented, explicitly conflicts with Spec, or lacks required verification evidence

## Output (strict format; no preamble, no long planning, no progress narration)

> ## Spec Alignment Review Report
> Feature: <feature>
> Spec Path: <path>
> Time: <timestamp>
>
> ### Summary
> Requirements: ✅x / ⚠️y / ❌z
> Design:       ✅x / ⚠️y / ❌z
> Tasks:        ✅x / ⚠️y / ❌z
> Verification: pass m/n (list failures)
>
> ### Spec Checklist (R/D/T)
> - R1: ...
> - D1: ...
> - T1: ...
>
> ### Alignment Table (must include every checklist item)
> | ID | Type | Spec Item (short) | Status | Evidence (code/output) | Gap / Impact |
> |----|------|-------------------|--------|-------------------------|--------------|
>
> ### Verification Log (each command + raw output)
> - V1: `<command>`
>   ```text
>   <raw output>
>   ```
>
> ### Action Items (prioritized)
> - P0: <IDs> Fix recommendation
> - P1: ...
> - P2: ...
