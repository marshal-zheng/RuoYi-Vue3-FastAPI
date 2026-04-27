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

if ! rg -n "setupMockServerLifecycle\\(\\)" tests/setup.ts >/dev/null; then
  echo "ERROR: tests/setup.ts must initialize the shared MSW lifecycle." >&2
  failed=1
fi

exit "$failed"

