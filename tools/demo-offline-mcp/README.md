# Demo Offline Data MCP

Repository-local TypeScript MCP server for demo-offline data generation workflows.

This package is a development tool. It is not imported by the Vue runtime, FastAPI backend, production build, or customer offline bundle. AI model calls and provider API keys stay outside this repository and are handled by the external MCP client or Chat Agent.

## Build And Start

```bash
cd tools/demo-offline-mcp
npm install
npm run build
npm test
npm run dev -- --repo-root ../..
```

For a built stdio server:

```bash
cd tools/demo-offline-mcp
npm run build
npm run start -- --repo-root ../..
```

The server uses stdio for the MCP protocol. Diagnostics go to stderr only; stdout is reserved for MCP messages.

## Audit Log

Every tool invocation writes a short diagnostic line to stderr and appends a JSONL audit record under the generated
candidate area:

```text
ruoyi-fastapi-frontend/src/demo/scenarios/generated/candidates/.audit/demo-offline-mcp.jsonl
```

Each record includes the tool name, phase (`started`, `succeeded`, or `failed`), resolved `repoRoot`,
`generatedRoot`, `candidateRoot`, runtime fingerprint, compact input identifiers, and compact output or error evidence.
Large draft and scenario payloads are summarized rather than logged in full. The `runtime` object records `pid`,
`processStartedAt`, `entrypoint`, Node version, current git head, and hashes/mtimes for the loaded MCP files. Use those
fields to identify stale stdio processes after rebuilding `dist`.

If a promote call used the current implementation, `demo_offline_promote_candidate` `succeeded` records should include
`output.data.activated` and `output.data.activePath` unless `activate: false` was explicitly passed. If a client reports
that a candidate was written, this file should show a matching `demo_offline_write_candidate` `succeeded` record with
the same `candidateId` and paths. If there is no matching record in this repository, the client likely did not call this
MCP instance or used a different `--repo-root`.

## MCP Client Config

Generic stdio configuration:

```json
{
  "mcpServers": {
    "demo-offline-data": {
      "command": "node",
      "args": [
        "/absolute/path/to/RuoYi-Vue3-FastAPI/tools/demo-offline-mcp/dist/index.js",
        "--repo-root",
        "/absolute/path/to/RuoYi-Vue3-FastAPI"
      ]
    }
  }
}
```

Cherry Studio and similar clients can use the same command/args shape. Keep model provider configuration in the client, not in this repository.

## Recommended Workflow

1. Call `demo_offline_scan_context` to collect supported demo-offline slices, handlers, scripts, scenarios, and risks.
2. Call `demo_offline_create_generation_plan` with an industry brief. P0 defaults to `project + simulation`; `auth/system` are copied from the default scenario.
3. Ask the external Chat Agent to produce an `IndustryDataDraft` from the plan.
4. Call `demo_offline_validate_draft`. If it returns issues, fix the draft using `path`, `code`, `expected`, and `fixHint`.
5. Call `demo_offline_compile_scenario` after validation passes.
6. Call `demo_offline_write_candidate` to write the candidate under `ruoyi-fastapi-frontend/src/demo/scenarios/generated/candidates/**`.
7. Call `demo_offline_run_checks` with the full candidate promote set in one run:
   `candidate-focused-tests`, `frontend-type-check`, and `candidate-demo-offline-build`.
8. After reviewing the candidate and checks, call `demo_offline_promote_candidate` with `confirm: true`.
   Promotion writes the official generated scenario, updates the generated registry, and by default activates the
   promoted scenario for demo-offline `auto` startup via `generated/active.ts`. Pass `activate: false` only when the
   scenario should be added to the library without becoming the default offline demo.

## Tool Permissions

| Tool | Access | Notes |
| --- | --- | --- |
| `demo_offline_scan_context` | read-only | Scans `ruoyi-fastapi-frontend/src/demo/**`, generated scenario state, and frontend scripts. |
| `demo_offline_create_generation_plan` | read-only | Produces a traceable plan from the brief and scan context. |
| `demo_offline_validate_draft` | read-only | Returns structured validation and repair guidance; never writes candidate files. |
| `demo_offline_compile_scenario` | read-only | Compiles a draft into a scenario package in memory. |
| `demo_offline_write_candidate` | writes files | Writes only generated candidate files and candidate metadata/registry. |
| `demo_offline_run_checks` | executes commands | Runs fixed named profiles only. No arbitrary shell command is accepted. |
| `demo_offline_promote_candidate` | writes files | Requires `checksRunId` and `confirm: true`; writes official generated scenario and registry. |

## Safety Boundaries

- No DeepSeek, Kimi, OpenAI, Gemini, or other provider API key is required or read by this package.
- Write access is restricted to `ruoyi-fastapi-frontend/src/demo/scenarios/generated/**`.
- The MCP never writes `src/demo/handlers/**`, `src/mocks/**`, Vue routes, business pages, real API code, or backend files.
- Candidate scenarios are not official until `demo_offline_promote_candidate` is explicitly called.
- Promoted scenarios become the active demo-offline scenario by default. `VITE_DEMO_SCENARIO_ID=auto` or an unset
  scenario ID uses that active pointer, while an explicit scenario ID still overrides it.
- Promote rejects incomplete check runs, mismatched candidate/scenario IDs, and candidates changed after checks.
- Existing official scenarios are not replaced unless `replaceExisting: true` is passed.
- If a candidate passes checks but is not promoted, the current official scenario remains unchanged.
- If an API is not covered by demo-offline handlers, the runtime keeps returning `DEMO_API_NOT_IMPLEMENTED`; the MCP does not create temporary handlers.

## Check Profiles

Allowed `demo_offline_run_checks` profiles:

```text
candidate-focused-tests
frontend-type-check
candidate-demo-offline-build
promoted-demo-offline-build
```

The runner executes commands in `ruoyi-fastapi-frontend/` using fixed command templates and environment variables. Requests for commands outside this list are rejected with the allowed profile list and suggested alternatives.

## Existing Commands Stay Usable

The MCP is optional. If no MCP client is configured, the existing frontend commands still work as before:

```bash
cd ruoyi-fastapi-frontend
yarn dev
yarn dev:mock
yarn build:prod
yarn build:demo-offline
```

## Future Extensions

Future Workbench, CLI, or AI provider integrations must reuse this MCP core or an equivalent shared core. API keys must not enter the browser runtime, production build, or customer `dist-demo-offline` package.
