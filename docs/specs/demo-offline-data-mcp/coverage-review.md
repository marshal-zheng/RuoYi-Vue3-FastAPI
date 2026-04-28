# Demo Offline Data MCP 完成度评估

评估时间：2026-04-28

验证证据：

- `tools/demo-offline-mcp`: `npm test` -> 9 files / 34 tests passed; `npm run build` -> passed.
- `ruoyi-fastapi-frontend`: `yarn test:run src/demo/scenarios/generated/*.test.ts src/demo/scenarios/index.test.ts src/demo/repositories/scenario.test.ts src/demo/services/project.test.ts src/demo/services/simulation.test.ts src/demo/handlers/project.test.ts src/demo/handlers/simulation.test.ts` -> 8 files / 26 tests passed.
- `ruoyi-fastapi-frontend`: `yarn build:prod` -> passed; output ended with `built in 22.96s`.
- Candidate acceptance: `runChecks` run `check-20260428025715` -> `candidate-focused-tests`, `frontend-type-check`, `candidate-demo-offline-build` all passed.
- Promoted acceptance: `runChecks` run `check-20260428030128` -> `frontend-type-check`, `promoted-demo-offline-build` passed; build output ended with `built in 23.30s`.
- `dist-demo-offline` scan: `rg -o "DeepSeek|Kimi|OpenAI|demo-offline-mcp|MODEL_PROVIDER|API_KEY|sk-[A-Za-z0-9]{20,}" dist-demo-offline` -> no matches. `Gemini` appears only in bundled music/zodiac fixture text, not provider config.

## Requirements

- R1.AC1 — covered — `tools/demo-offline-mcp/src/index.ts` creates stdio `McpServer`; `tests/mcp-stdio.test.ts` lists tools and calls `demo_offline_scan_context` over stdio.
- R1.AC2 — covered — MCP source is under `tools/demo-offline-mcp/**`; `rg "tools/demo-offline-mcp|demo-offline-mcp" ruoyi-fastapi-frontend/src ruoyi-fastapi-backend` returned no runtime imports.
- R1.AC3 — covered — `src/project-paths.ts` bounds repo paths; `src/demo-scan.ts` scans `src/demo/**` and frontend scripts; `tests/project-paths.test.ts` covers traversal/symlink escape.
- R1.AC4 — covered — no frontend/backend runtime import of tool package; `build:demo-offline` passed with no MCP code match in `dist-demo-offline`.
- R1.AC5 — covered — existing scripts remain in `ruoyi-fastapi-frontend/package.json`; focused tests, type-check, and `build:demo-offline` passed after registry changes.
- R2.AC1 — covered — `src/config.ts` has no provider key requirement; `tests/config.test.ts` asserts no API key requirement.
- R2.AC2 — covered — README states model calls stay in external clients; no frontend/backend model-provider integration was added.
- R2.AC3 — covered — validator/check tools return structured `ToolEnvelope` issues/results; no model API calls exist under `tools/demo-offline-mcp/src`.
- R2.AC4 — covered — final `dist-demo-offline` scan found no DeepSeek/Kimi/OpenAI/MCP/API-key patterns.
- R3.AC1 — covered — `src/demo-scan.ts` reads schema/default/index/repository/handlers; `tests/demo-scan.test.ts` asserts scenarios, handlers, scripts, risks.
- R3.AC2 — covered — `DemoOfflineContext` in `src/types.ts` includes safe slices, copied slices, scenarios, scripts, risks.
- R3.AC3 — covered — scanner uses `paths.demoRoot` and frontend package scripts, not `src/views/**`, `src/api/**`, or backend code.
- R3.AC4 — covered — `formatDemoOfflineContext` returns compact summaries and evidence paths, not source bodies.
- R3.AC5 — covered — scanner distinguishes `default`, `generated`, and `candidate`; tested in `tests/demo-scan.test.ts`.
- R3.AC6 — covered — scan risks include unsupported slices and catch-all behavior; planner marks unsupported full-module requests.
- R4.AC1 — covered — `src/generation-plan.ts` emits structured plan with generate/copy/unsupported trace.
- R4.AC2 — covered — all-module briefs only include safe slices as generated; unsupported modules are trace items.
- R4.AC3 — covered — `p0-unsupported-business-modules` trace documents P0 unsupported scope.
- R4.AC4 — covered — every trace entry includes evidence paths or explicit scan-scope evidence.
- R4.AC5 — covered — planner normalizes local scope and auto-adds `project` when `simulation` is requested; tested.
- R4.AC6 — covered — default scope is `project + simulation`, copied slices are `auth/system`; tested.
- R5.AC1 — covered — `IndustryDataDraft` schema/tool is the draft input; compiler consumes draft, not AI-authored final package.
- R5.AC2 — covered — compiler generates deterministic IDs/times/fingerprint/relationships; `tests/compiler.test.ts` asserts stable output.
- R5.AC3 — covered — compiler/validator default `scenario.version`, owner names, versions, topology, simulation records.
- R5.AC4 — covered — validator detects invalid enums, placeholders, duplication, industry mismatch, topology gaps; tests cover representative failures.
- R5.AC5 — covered — compiler validates array package structure and writes only data; no handlers/routes/API/IndexedDB scripts generated.
- R5.AC6 — covered — generic `IndustryDataDraft` schema exists; `real-estate-p0-acceptance-demo` is the first acceptance sample.
- R5.AC7 — covered — schema/planner/compiler use generic industry fields and tests include non-real-estate planning branches.
- R6.AC1 — covered — `ValidationIssue` includes path/code/actual/expected/fixHint/autoRepairable; validator tests assert these fields.
- R6.AC2 — covered — auto-repair warnings return repaired draft and repair summary for whitespace/version/ownerName.
- R6.AC3 — covered — placeholder and semantic issues return concrete fix hints.
- R6.AC4 — covered — validation failure does not call writer; candidate write is a separate explicit tool.
- R6.AC5 — covered — `scope_not_supported_by_scan` reports missing scan coverage; tested.
- R7.AC1 — covered — `ProjectPaths.resolveGeneratedWritePath` and writer tests enforce generated-only writes.
- R7.AC2 — covered — `writeCandidateScenario` writes `generated/candidates/*.candidate.ts` before official files.
- R7.AC3 — covered — promote requires passed check run; missing/failed checks reject.
- R7.AC4 — covered — `demo_offline_promote_candidate` requires `checksRunId` and `confirm: true`.
- R7.AC5 — covered — main `src/demo/scenarios/index.ts` merges `generatedScenarioRegistry`; writer updates only generated registries.
- R7.AC6 — covered — candidate and official conflict paths reject unless explicit overwrite/replace is passed.
- R7.AC7 — covered — writer tests confirm candidate write does not create official file before promote.
- R8.AC1 — covered — `candidate-focused-tests` runs generated scenario/repository/service/handler focused tests.
- R8.AC2 — covered — `frontend-type-check` profile and final acceptance type-check passed.
- R8.AC3 — covered — candidate and promoted build profiles run `yarn build:demo-offline`; both passed.
- R8.AC4 — covered — `CheckResult` includes command, exitCode, stdout/stderr tails, and nextActions; failure tested.
- R8.AC5 — covered — `RunChecksResult` includes scenario/candidate id, runMode, recommended preview command, and command artifacts; tested.
- R8.AC6 — covered — success nextActions still require explicit promote for candidates.
- R8.AC7 — covered — real-estate P0 candidate generated, validated, tested, built, and promoted.
- R8.AC8 — covered — allowlist profiles are fixed; arbitrary profile rejects with allowed alternatives.
- R9.AC1 — covered — changed paths are tools, generated scenarios/registries, runtime mode plumbing, and tests; no handlers/routes/API/backend production code generated by MCP writer.
- R9.AC2 — covered — generated scenario tests use `getDemoScenarioPackage`, `ScenarioRepository.ensureScenario`, services, and handlers.
- R9.AC3 — covered — `DEMO_API_NOT_IMPLEMENTED` catch-all unchanged; scanner reports it and handler tests pass.
- R9.AC4 — covered — runtime mode tests cover real/fallback semantics; type-check/build passed.
- R9.AC5 — covered — README requires future Workbench/CLI/provider integrations to reuse MCP core.
- R10.AC1 — covered — README documents build/start commands.
- R10.AC2 — covered — README includes stdio client config and recommended workflow.
- R10.AC3 — covered — README tool matrix marks read/write/execute tools.
- R10.AC4 — covered — README documents write directory, command allowlist, and explicit promote confirmation.
- R10.AC5 — covered — README states API keys must not enter browser runtime or customer offline bundle.
- R10.AC6 — covered — `runChecks` rejects non-allowlist profiles; test asserts structured allowed-profile guidance.

## Design

- Architecture overview — covered — implemented in `tools/demo-offline-mcp/**`, no provider keys, stdio tools, generated-only writes, existing runtime chain preserved.
- Directory structure — covered — package files, source modules, tests, frontend generated/candidates registries, official scenario/test files exist.
- Generated registry integration — covered — `src/demo/scenarios/index.ts`, `generated/index.ts`, and `generated/candidates/index.ts`.
- Tech choices — covered — MCP SDK `registerTool`, Zod schemas, TypeScript, structuredContent, annotations, named check profiles.
- Data flow — covered — scan -> plan -> validate -> compile -> write candidate -> run checks -> promote executed for real-estate P0.
- MCP Server Entry — covered — `src/index.ts` parses `--repo-root`, registers all tools, logs to stderr.
- ToolEnvelope — covered — `src/types.ts` and tool handlers return `structuredContent`.
- ProjectPaths — covered — `src/project-paths.ts`; path tests cover repo root, generated write allowlist, traversal, symlink escape.
- DemoScanner — covered — `src/demo-scan.ts`; tests cover schema/default/handlers/scripts/scenarios/risks.
- GenerationPlanner — covered — `src/generation-plan.ts`; tests cover defaults, local scope dependency, unsupported full-module request, counts.
- DraftSchema/Validator — covered — `src/draft-schema.ts`, `src/validator.ts`; tests cover structural/semantic/context/relationship/repair cases.
- ScenarioCompiler — covered — `src/compiler.ts`; tests cover deterministic output, auth/system copy, arrays, linked IDs.
- ScenarioWriter — covered — `src/writer.ts`; tests cover candidate write, conflicts, passed-check promote, official replace, cleanup.
- CheckRunner — covered — `src/checks.ts`; tests cover allowlist, env/command templates, failure summaries, required ids.
- API tools — covered — all seven `demo_offline_*` tools registered and stdio-smoke-tested.
- Data model / DB changes — covered — no backend migration; generated files only under frontend demo scenarios and tools package.
- Security considerations — covered — provider-free, generated-only writes, no shell, no runtime import, explicit promote, structured errors.
- Testing strategy — covered — MCP unit tests, frontend generated/import/service/handler tests, type-check, candidate/promoted build, dist scan.

## Tasks

- Task 1 — covered — tools package skeleton, stdio server, scripts, envelope, no provider key; `npm test/build` passed.
- Task 2 — covered — ProjectPaths/security/error model with tests.
- Task 3 — covered — generated/candidate registries, runtime candidate option, `dev:demo-offline`, frontend registry tests.
- Task 4 — covered — scan tool/context/risks with tests.
- Task 5 — covered — generation plan tool with trace, default scope, unsupported full-module handling, tests.
- Task 6 — covered — draft schema/validator/repair report with tests.
- Task 7 — covered — deterministic compiler with tests.
- Task 8 — covered — candidate writer/promote/check gate/conflict handling with tests.
- Task 9 — covered — fixed allowlist check runner with tests and real acceptance runs.
- Task 10 — covered — all MCP tools registered; stdio client smoke test lists/calls tools.
- Task 11 — covered — README documents config, workflow, tool permissions, boundaries, future API-key rule.
- Task 12 — covered — MCP unit tests and frontend integration/focused tests passed.
- Task 13 — covered — real-estate P0 workflow ran through failed validation report, repair, compile, candidate checks, promote, final type-check/build, and dist scan.

Remaining gaps/risks: 无。Build warnings remain existing Browserslist/chunk-size warnings, not task-blocking failures.
