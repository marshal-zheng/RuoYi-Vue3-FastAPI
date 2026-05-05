#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

failed=0

if rg -n "@ts-nocheck" src/mocks; then
  echo "ERROR: src/mocks must not use @ts-nocheck." >&2
  failed=1
fi

if rg -n "vi\\.mock\\(['\\\"]@/utils/request" src tests --glob '!tests/reports/**'; then
  echo "ERROR: tests must not mock '@/utils/request'; use MSW for HTTP contract behavior." >&2
  failed=1
fi

if [[ -f tests/mocks/api-contract-handlers.ts ]]; then
  echo "ERROR: tests/mocks/api-contract-handlers.ts must not reintroduce a parallel HTTP contract; use src/mocks handlers." >&2
  failed=1
fi

if rg -n "http\\.(get|post|put|patch|delete|all)\\(" tests --glob '!tests/mocks/**' --glob '!tests/e2e/**' --glob '!tests/reports/**'; then
  echo "ERROR: tests must not define private HTTP contract handlers; register page-state behavior as src/mocks/overlays entries or use shared harnesses." >&2
  failed=1
fi

if rg -n "VITE_DEMO_SCENARIO_ID|VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS|__DEMO_RUNTIME__|candidate/promote|active pointer" src tests scripts --glob '*.{ts,tsx,js,jsx,vue,sh,mjs}' --glob '!**/*.test.ts' --glob '!tests/reports/**' --glob '!src/mocks/runtime/app-entry.ts' --glob '!scripts/check-mock-standards.sh'; then
  echo "ERROR: legacy scenario runtime activation must not be used for mock overlays." >&2
  failed=1
fi

if ! rg -n "create(Status|Network|Timeout)Handler" src/mocks/handlers/error-common.ts >/dev/null; then
  echo "ERROR: shared MSW error handlers must live in src/mocks/handlers/error-common.ts." >&2
  failed=1
fi

if ! rg -n "error-timeout|error-5xx|error-429" src/mocks/handlers/error-common.ts src/mocks/scenarios/error.ts src/mocks/scenarios/index.ts >/dev/null; then
  echo "ERROR: mock error scenarios must be registered in src/mocks/scenarios." >&2
  failed=1
fi

if ! rg -n "setupMockServerLifecycle\\(\\)" tests/setup.ts >/dev/null; then
  echo "ERROR: tests/setup.ts must initialize the shared MSW lifecycle." >&2
  failed=1
fi

exit "$failed"
