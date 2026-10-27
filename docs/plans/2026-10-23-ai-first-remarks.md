# AI-first Remarks Implementation Plan

> 历史记录：旧场景协议已由 AICONTEXT 替换，不作为当前部署说明。当前行为见 [实施记录](../reports/aicontext-implementation.md) 与 [部署说明](../../ruoyi-fastapi-backend/docs/text-field-ai-deployment.md)。本轮未执行浏览器或真实模型验收。

WORK_ITEM: none

**Goal:** Deliver AI drafting and whole-remark/selection rewriting through the actual business backend, with a persistent compact formatting toolbar and explicit candidate acceptance.
**Inputs:** User-approved interaction proposal on 2026-10-23; `docs/specs/generic-remark-rich-text/requirements.md`; the shared RemarkEditor; ZXUI TextEditorField and authoring primitives; existing authenticated HTTP/session infrastructure. This repository has no steering directory.
**Scope Boundaries:** All seven migrated management remark scenes; reusable field UI and application semantics in ZXUI; authenticated server-side DeepSeek generation; typed frontend transport; scene-specific context; cancellation, validation and real local verification. No database migration, record auto-save, general chat platform, multi-provider administration, or unrelated domain remark migration.
**Assumptions:** Reuse the existing configured DeepSeek endpoint and model. Secrets stay on the server. Existing unrelated workspace changes are preserved. Work is performed in the current shared checkouts because the user's active local app consumes those source changes.

## Task List

### Task 1: Implement reusable field authoring and formatting

**Files:**
- Modify: `/Users/hqz/Downloads/element-plus/packages/text-editor/src/text-editor-field.vue`
- Create: field AI contract, controller and presentation files under that package
- Test: field AI and toolbar tests under the package's `__tests__/`

**Steps:**
1. Define a narrow provider adapter that accepts an instruction and captured target, supports abort and text deltas, and returns a validated document.
2. Reuse existing authoring/application and formatting primitives for a persistent AI-first toolbar and inline candidate panel.
3. Capture whole-document or selection targets without changing the document while streaming.
4. Validate the full merged result, reject stale targets, and apply accepted changes as one undoable transaction.
5. Cancel work on disable, disposal or session capture and protect IME input.

**Verification:**
- Run: `pnpm exec vitest --config packages/text-editor/vitest.config.mts --run <affected test files>` from the ZXUI root.
- Run: `pnpm -C packages/text-editor typecheck` from the ZXUI root.
- Expect: drafting, selection preservation, stale rejection, cancellation, formats and one-step undo pass.

**Dependencies:** none
**Output:** Public typed field AI API, working compact UI and regression evidence.

### Task 2: Implement the authenticated server generation boundary

**Files:**
- Create: `ruoyi-fastapi-backend/modules/system/api/remark_ai_controller.py`
- Create: remark AI application service and request models
- Modify: backend router registration and server settings
- Test: targeted backend remark AI service and HTTP contract tests

**Steps:**
1. Reuse server authentication, response contracts and installed HTTP streaming facilities.
2. Validate scene-specific context and the existing remark document format before sending a bounded prompt.
3. Stream candidate text and emit a validated canonical document on completion.
4. Handle cancellation, missing configuration, provider errors, malformed output and incomplete generations explicitly.
5. Document server-only configuration without exposing credential values.

**Verification:**
- Run: `./venv/bin/python -m pytest tests/unit/services/test_remark_ai_service.py -q` from the backend, adjusted to the final test path.
- Run: `./venv/bin/ruff check <changed Python files>` and `./venv/bin/ruff format --check <changed Python files>`.
- Expect: valid results satisfy remark-a-v1; invalid/incomplete results never claim success; errors do not expose secrets or prompts.

**Dependencies:** none
**Output:** Authenticated generation endpoint and server-side provider configuration.

### Task 3: Integrate business transport and all remark callers

**Files:**
- Create: `ruoyi-fastapi-frontend/src/api/system/remarkAi.ts`
- Modify: `ruoyi-fastapi-frontend/src/components/ui/Remark/RemarkEditor.vue`
- Create: remark AI scene/context definitions and tests
- Modify: user, role, post, dictionary type/data, configuration and generator remark callers

**Steps:**
1. Adapt the existing SSE parser with business authentication, session cancellation and no automatic generation retries.
2. Supply the field's AI adapter through the shared RemarkEditor wrapper.
3. Capture only explicitly allowed business fields at generation time, preserving SchemaForm as the owner of post values.
4. Keep close/save guards aware of pending AI input and candidates without auto-saving records.
5. Verify error, retry, cancellation and successful result propagation through real component contracts.

**Verification:**
- Run: `./node_modules/.bin/vitest run src/api/system/remarkAi.test.ts` from the frontend.
- Run: `VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus ./node_modules/.bin/vitest run --config vitest.remark-source.config.ts` from the frontend.
- Expect: every migrated scene receives AI; confidential or arbitrary form fields are excluded; accepted results alone update the remark.

**Dependencies:** Task 1 and Task 2 contracts
**Output:** Complete browser-to-server-to-field integration for the seven remark scenes.

### Task 4: Regenerate contracts and validate the actual local workflow

**Files:**
- Modify: `shared/openapi.json` and frontend generated API outputs through their generators
- Modify: remark documentation and the superseded interaction decision
- Create: concise verification report under `docs/reports/`

**Steps:**
1. Generate OpenAPI and API types from the actual backend routes.
2. Safely configure local server credentials using existing local configuration; restart only the relevant development service when needed.
3. Exercise a synthetic remark through the real authenticated API and model.
4. Verify empty drafting, whole/selection rewriting, format actions, cancellation and undo in user/post forms without saving business records.
5. Reconcile child changes, run focused lint/type checks, and record any unverified boundaries precisely.

**Verification:**
- Run: backend `scripts/export_openapi.py` and root `scripts/generate-api-types.sh --artifact`.
- Run: frontend `./node_modules/.bin/vue-tsc --noEmit` plus focused ESLint and backend checks.
- Expect: real generation works, provider credentials never enter browser requests, dialogs retain usable layout, and existing remark roundtrips pass.

**Dependencies:** Tasks 1, 2 and 3
**Output:** Integrated implementation and separate automated, real-model and browser verification evidence.

## Execution Handoff

Continue current-session execution immediately: the user explicitly approved the solution and full implementation. The parent owns business integration, generated artifacts and final reconciliation. Library, backend and frontend transport agents are parent-observed with disjoint file ownership; their summaries are not substitutes for verified evidence. No commits, publishing or record creation are requested.

## Status Sync Suggestion

No work-item ledger is bound. Track task results here and in the verification report. Do not claim completion until actual integration and applicable checks have been reconciled.

## Execution Result — 2026-10-23

Tasks 1–4 are complete. The shared field, authenticated server streaming, all seven business callers and generated contracts are integrated. The frontend consumes the local release artifact `1.0.0-remark-ai.20261023.2`; it has not been published. Real DeepSeek/browser verification covered user and post forms, drafting, selection rewrite, candidate refinement, adoption/undo, stale protection and cancellation. Browser findings (duplicate selection bubble obscuring the fixed toolbar, pending review causing stale validation errors) were fixed and regression-tested. See [verification evidence](../reports/2026-10-23-ai-first-remarks.md) for checks and remaining boundaries. No business records were saved and no commits or external releases were performed.
