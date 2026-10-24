# Schema Task Authoring Implementation Plan

**Goal:** Deliver task-oriented schema authoring documentation without reducing the public contract, then measure its effect with an otherwise identical AI authoring experiment.
**Inputs:** `docs/reports/schema-aria-ai-closeout-2026-10-20.md`; ZXUI `packages/schema-form/README.md`, public types, exercised pilot recipes; the prior frozen AI protocol and corrected checker.
**Scope Boundaries:** ZXUI documentation and documentation packaging; local evidence and reports. No schema runtime/API reduction, business patches, browser automation, publication, or commits.
**Assumptions:** The prior ordinary CRUD task remains the controlled token comparison. Complex capability preservation is independently audited against source and existing integration cases, not inferred from the CRUD experiment.

## Task List

### Task 1: Preserve the baseline and organize authoring tasks

**Files:**
- Modify: ZXUI `packages/schema-form/README.md`
- Create: ZXUI `packages/schema-form/docs/authoring/{crud,composite-fields,nested-errors,controlled-fields,json-import,reference}.md`
- Create: `docs/reports/evidence/schema-task-authoring-2026-10-20/baseline.json`

**Steps:**
1. Preserve the complete previous README and runtime source hashes.
2. Create a short task router and practical task guides, using public APIs and existing exercised recipes.
3. Retain the full contract in a reference with explicit links from task guides.
4. Audit single-owner state, lifecycle, cancellation, nested identity, raw/canonical values, accessibility, engine isolation and JSON admission.

**Verification:**
- Run: `git diff --check -- packages/schema-form`
- Expect: no whitespace errors; a reviewed capability mapping covers every former contract section.

**Dependencies:** none
**Output:** task guides, complete reference and baseline evidence.

### Task 2: Ship documentation with the actual package

**Files:**
- Modify: ZXUI `packages/schema-form/scripts/copy-examples.mjs`, `packages/schema-form/package.json` if needed
- Create: evidence verification scripts/logs under `docs/reports/evidence/schema-task-authoring-2026-10-20/`

**Steps:**
1. Extend the existing documentation/example delivery step; do not create a documentation platform.
2. Rewrite repository-relative recipe/type links to the corresponding packaged examples/declarations.
3. Build and inspect an actual local tarball for complete, resolving documentation links.
4. Verify unchanged runtime source hashes and run existing focused integration checks for the documented complex paths.

**Verification:**
- Run in ZXUI: `pnpm -C packages/schema-form typecheck`
- Run in ZXUI: `pnpm -C packages/schema-form build`
- Run in ZXUI: `node docs/research/schema-form-pilot/pilot/run.mjs test`
- Run: local tarball/link/hash verification recorded in the evidence directory.
- Expect: all task guides and the full reference ship; examples/types resolve; existing complex cases pass; runtime source is unchanged.

**Dependencies:** Task 1
**Output:** a verified local package and retained capability evidence.

### Task 3: Freeze and run the controlled AI comparison

**Files:**
- Create: `docs/reports/evidence/schema-task-authoring-2026-10-20/ai-authoring/`

**Steps:**
1. Keep the previous task, domain, output schema, model, effort, CLI, no-tool settings and ABBA order.
2. Compare the previous full README against the new README plus CRUD guide, with identical public types and artifact declarations.
3. Freeze the corrected checker, exact harmless CLI warning handling, and all input hashes before model calls.
4. Run four first attempts without retries or manual source repair; record every failure.
5. Independently score each result and compute actual usage, quality, paired differences and limitations.

**Verification:**
- Run: `python3 docs/reports/evidence/schema-task-authoring-2026-10-20/ai-authoring/run.py`
- Run: `python3 docs/reports/evidence/schema-task-authoring-2026-10-20/ai-authoring/run.py --execute`
- Expect: frozen inputs verify; all four attempts remain auditable regardless of outcome.

**Dependencies:** Tasks 1 and 2
**Output:** matched results and raw evidence, with no unsupported universal efficiency claim.

### Task 4: Review and report

**Files:**
- Create: `docs/reports/schema-task-authoring-2026-10-20.md`
- Update: this plan with completion evidence.

**Steps:**
1. Review documentation and packaging changes independently.
2. Verify source, artifact, prompt, checker and raw result hashes.
3. Report quality and token outcomes separately, including unsuccessful samples and scope limits.

**Verification:**
- Run: evidence hash checks and `git diff --check` for affected files.
- Expect: report claims match preserved artifacts and actual command results.

**Dependencies:** Task 3
**Output:** a self-contained delivery report.

## Progress

- [x] Task 1 baseline preserved.
- [x] Task 1 documentation and capability audit: 7 documents, 18 capability groups, original behavioral reference retained.
- [x] Task 2 package delivery and focused verification: typecheck/build, 14 pilot cases, 56 packaged links and 5 unchanged recipes.
- [x] Task 3 controlled comparison and independent quality review: four valid first attempts; both arms 2/2 functional acceptance, zero repairs/retries.
- [x] Task 4 final evidence audit and report: see `docs/reports/schema-task-authoring-2026-10-20.md` and the evidence verification record.

Task 3 inputs and checker were frozen before calls. Manifest SHA-256:
`3f49d0d4b28181e04bd74121d237f84665cdfb63e209491b9944ea685971947e`.
Both groups share tarball SHA-256:
`25ea9886e966d3fe8b036421073f344d72ca65949c93cbc590ca47053905319b`.

Observed input fell 4.51%; mean total fell only 0.71%, with opposite paired
directions and higher mean latency. Stable total-token or speed improvement was
not demonstrated. Functional acceptance does not prove identical interaction
design: full-docs answers used a status select; task-docs answers used an input
with enum validation. These allowed differences remain in the quality report.

## Design evidence

Borrow the separation between task-oriented how-to guides and complete reference from [Diátaxis how-to guides](https://diataxis.fr/how-to-guides/) and [reference](https://diataxis.fr/reference/). Use the existing Markdown/build structure instead of adopting a new documentation framework. These sources support organization, not token-saving claims.

Follow [OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices) by defining task-specific quality checks and comparing changes under fixed conditions. The actual token outcome comes only from recorded model usage.
