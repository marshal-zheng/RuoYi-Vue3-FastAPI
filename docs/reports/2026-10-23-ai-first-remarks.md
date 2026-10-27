# AI-first remark verification

> 历史记录：旧场景协议已由 AICONTEXT 替换，不作为当前部署说明。当前行为见 [实施记录](../reports/aicontext-implementation.md) 与 [部署说明](../../ruoyi-fastapi-backend/docs/text-field-ai-deployment.md)。本轮未执行浏览器或真实模型验收。

## Scope and evidence boundaries

The approved change covers the seven existing management remark scenes, shared ZXUI field UI, authenticated business transport and the server-side DeepSeek service. No business records are created or saved during browser verification. Synthetic instructions are used for real provider requests.

## Browser QA inventory

- Empty field: visible AI entry and compact formatting controls; generating a synthetic draft streams readable text and leaves the original empty until acceptance.
- Existing field: whole-remark rewrite, refinement of the candidate, adoption and one-step undo.
- Selection: captured range remains the only replacement target; surrounding text is unchanged.
- Formatting: bold, named color, unordered/ordered lists, link and the more menu; keyboard undo and return to unformatted text.
- Pending work: stop generation, discard a candidate, close/reopen the form and confirm no late or residual content.
- Off-happy-path: edit original while a candidate is pending; prevent stale acceptance. Close a form during generation and verify cancellation.
- Native user form and SchemaForm post dialog: same field behavior, current business context, normal editing without spurious validation errors.
- Visual checks: initial toolbar, prompt and candidate states; light and dark appearance; constrained width; overlay hit testing and absence of horizontal clipping.

## Results

Implementation and local integration are complete. The business frontend now references `vendor/zxio-text-editor-1.0.0-remark-ai.20261023.2.tgz`. This is a local build, not a registry release or production deployment.

### Automated checks

| Boundary | Result |
| --- | --- |
| Text-editor package: basic field, AI lifecycle, bubble overlay | 30 passed; package typecheck and build passed |
| Frontend remark integration, Formily and document roundtrip | 37 passed across 3 files |
| Frontend authenticated SSE transport and session | 35 passed, including the real Axios fetch adapter |
| Backend service, HTTP contract and router registry | 52 passed: 41 service, 6 HTTP, 5 registry |
| Business `vue-tsc --noEmit` and changed-file ESLint | Passed |
| Backend changed-file Ruff and format | Passed; `config/env.py` retains its 32 existing lint diagnostics, with zero added |
| Generated OpenAPI and frontend API types | Generated successfully from the backend routes |

Frontend source checks used `VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus ./node_modules/.bin/vitest run --config vitest.remark-source.config.ts`. Transport/session checks used their two colocated test files. Backend checks used `./venv/bin/python -m pytest tests/unit/services/test_remark_ai.py tests/unit/services/test_remark_ai_http.py tests/unit/modules/test_registry.py -q --no-cov -n 0`. Library checks used its package-local Vitest configuration and `pnpm build`.

The library build still prints five existing declaration diagnostics from the root `tag-core.vue` dependency; it completes successfully, as do its own typecheck and declaration/export boundary checks. Source-mode frontend tests retain existing Vue test-host ref warnings. Neither is presented as a clean repository-wide gate.

### Actual browser and model results

- Used the normal local login and real FastAPI-to-DeepSeek requests, not mocked responses. Synthetic instructions produced readable candidates; a sampled completed response contained 12 `delta` events followed by `result` with HTTP 200.
- Empty user remark stayed empty during drafting. Refinement changed a candidate into three list items before adoption. Adoption updated the form, one undo restored the empty remark, and redo restored the accepted content.
- Selected `设备巡检。` inside `前文保留。设备巡检。后文保留。`; the real model returned `每日设备巡检。`. Adoption preserved both surrounding segments, and one undo restored the selected original.
- Editing the original after generation made the candidate stale and disabled adoption. Discard preserved the manual edit. The final native form check showed no remark validation errors before or after discard; explicit pending-submit rejection is covered by the real ElForm integration regression.
- Post SchemaForm sent `scene=post` with the current synthetic post name/code/status, generated and adopted a real candidate, stopped generation without changing the original, and confirmed discard on close. Reopening produced an empty remark with no retained AI panel.
- Directly exercised bold, named color, unordered/ordered lists, italic, clear marks and link insertion. The verified link was `https://example.com/inspection`. The duplicate selection bubble was removed only from the field; normal document-editor bubble tests still pass.
- Light desktop and dark constrained layouts were inspected. At a 640-pixel viewport the field measured 474 pixels wide with `scrollWidth === clientWidth`; AI action controls remained reachable through the dialog's normal scrolling. No page JavaScript errors were observed.

### Screenshots

- [User AI candidate](evidence/2026-10-23-ai-first-remarks/remark-candidate-final.png)
- [Post candidate, light](evidence/2026-10-23-ai-first-remarks/post-candidate-light.png)
- [Post prompt, dark, 640-pixel viewport](evidence/2026-10-23-ai-first-remarks/post-dark-640.png)

### Verified scope and remaining boundaries

All seven callers (user, role, post, dictionary type/data, configuration and generator table) were inspected for adapter/context wiring and checked by TypeScript. Manual browser checks focused on the two distinct form owners: native user form and post SchemaForm. The other five were not each exercised against the model. Cancellation, authorization, missing credentials, incomplete provider output and invalid documents have automated coverage; no claim is made that every provider failure was manually reproduced.

No create/update form was submitted. No production data migration, npm publishing, remote deployment or Git commit was performed. Server credentials are used from the process environment; deployment setup is documented in [AI service configuration](../../ruoyi-fastapi-backend/docs/text-field-ai-deployment.md). Existing unrelated workspace changes were preserved.
