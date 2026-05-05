#!/usr/bin/env bash
# Verify the contract-first single-dataset mock mainline boundaries.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_ROOT="$PROJECT_ROOT/ruoyi-fastapi-frontend"
FRONTEND_SRC="$FRONTEND_ROOT/src"
MOCK_ROOT="$PROJECT_ROOT/ruoyi-fastapi-frontend/src/mocks"
DIST_DEMO_OFFLINE="$PROJECT_ROOT/ruoyi-fastapi-frontend/dist-demo-offline"
DIST_PROD="$PROJECT_ROOT/ruoyi-fastapi-frontend/dist"

LEGACY_RUNTIME_PATTERN='(@/demo|src/demo|VITE_ENABLE_MOCK|VITE_DEMO_SCENARIO_ID|VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS|demo-offline-contract|demo-contract|demo-scenarios|tools/demo-offline-mcp|DemoScenarioPackage|ScenarioRepository|generatedScenarioRegistry|candidateScenarioRegistry|activeGeneratedScenarioId|release-store)'
LEGACY_ENV_PATTERN='(VITE_ENABLE_MOCK|VITE_DEMO_SCENARIO_ID|VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS)'
LEGACY_DOC_PATTERN='(MCP promote|generated/active\.ts|candidateScenarioRegistry|activeGeneratedScenarioId|release-store|runtime package writer)'

require_dist=false

usage() {
  cat <<'EOF'
Usage: scripts/check-mock-mainline.sh [--require-dist]

Options:
  --require-dist  Fail when dist-demo-offline is missing, and scan it with ignore rules disabled.
  -h, --help      Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --require-dist)
      require_dist=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

failures=0

report_failure() {
  local title="$1"
  local body="$2"
  failures=$((failures + 1))
  printf '\n[FAIL] %s\n%s\n' "$title" "$body" >&2
}

run_rg_check() {
  local title="$1"
  local pattern="$2"
  shift 2
  local output
  if output="$(rg -n --glob '*.{ts,tsx,js,jsx,vue}' "$pattern" "$@" 2>/dev/null || true)"; then
    if [[ -n "$output" ]]; then
      report_failure "$title" "$output"
    fi
  fi
}

run_rg_any_check() {
  local title="$1"
  local pattern="$2"
  shift 2
  local output
  if output="$(rg --no-ignore -n -o "$pattern" "$@" 2>/dev/null || true)"; then
    if [[ -n "$output" ]]; then
      report_failure "$title" "$output"
    fi
  fi
}

scan_build_output() {
  local output_dir="$1"
  local label="$2"

  if [[ ! -d "$output_dir" ]]; then
    return
  fi

  run_rg_any_check \
    "$label must not contain legacy runtime/env identifiers" \
    "$LEGACY_RUNTIME_PATTERN" \
    "$output_dir"

  bundle_sensitive_lines="$(
    rg --no-ignore -n -o -i \
      'tools/demo-offline-mcp|demo_offline_|openai|anthropic|dashscope|deepseek|model provider|modelProvider|OPENAI_API_KEY|ANTHROPIC_API_KEY|DASHSCOPE_API_KEY|api[_-]?key|apikey' \
      "$output_dir" 2>/dev/null || true
  )"
  if [[ -n "$bundle_sensitive_lines" ]]; then
    report_failure "$label must not contain legacy MCP or AI provider secrets/config" "$bundle_sensitive_lines"
  fi

  dist_legacy_artifacts="$(
    find "$output_dir" \( -path '*/demo-contract' -o -path '*/demo-contract/*' -o -path '*/demo-scenarios' -o -path '*/demo-scenarios/*' \) -print 2>/dev/null || true
  )"
  if [[ -n "$dist_legacy_artifacts" ]]; then
    report_failure "$label must not emit legacy scenario artifacts" "$dist_legacy_artifacts"
  fi
}

if [[ -e "$FRONTEND_SRC/demo" ]]; then
  report_failure \
    "legacy src/demo runtime must be removed" \
    "$FRONTEND_SRC/demo still exists; current mock runtime must live under src/mocks/** only."
fi

legacy_surface_lines="$(
  rg -n --glob '*.{ts,tsx,js,jsx,vue,json}' \
    --glob '!**/no-legacy-import.test.ts' \
    --glob '!tests/reports/**' \
    "$LEGACY_RUNTIME_PATTERN" \
    "$FRONTEND_SRC" \
    "$FRONTEND_ROOT/tests" \
    "$FRONTEND_ROOT/vite" \
    "$FRONTEND_ROOT/vite.config.ts" \
    "$FRONTEND_ROOT/package.json" 2>/dev/null || true
)"
if [[ -n "$legacy_surface_lines" ]]; then
  report_failure "current frontend runtime must not reference legacy demo/scenario paths" "$legacy_surface_lines"
fi

frontend_env_files=()
while IFS= read -r env_file; do
  frontend_env_files+=("$env_file")
done < <(find "$FRONTEND_ROOT" -maxdepth 1 -type f -name '.env*' -print | sort)
if (( ${#frontend_env_files[@]} > 0 )); then
  run_rg_any_check \
    "frontend env files must not define legacy mock runtime switches" \
    "$LEGACY_ENV_PATTERN" \
    "${frontend_env_files[@]}"

  run_rg_any_check \
    "frontend env files must not describe legacy scenario/MCP workflows" \
    "$LEGACY_DOC_PATTERN" \
    "${frontend_env_files[@]}"
fi

if [[ ! -d "$MOCK_ROOT" ]]; then
  report_failure "src/mocks directory missing" "$MOCK_ROOT does not exist"
else
  run_rg_check "src/mocks must not disable TypeScript checks" '@ts-nocheck' "$MOCK_ROOT"

  legacy_imports="$(
    rg -n --glob '*.{ts,tsx,js,jsx,vue}' \
      --glob '!**/*.test.ts' \
      '(@/demo/scenarios|tools/demo-offline-mcp|DemoScenarioPackage|ScenarioRepository)' \
      "$MOCK_ROOT" 2>/dev/null || true
  )"
  if [[ -n "$legacy_imports" ]]; then
    report_failure "src/mocks must not import legacy scenario runtime" "$legacy_imports"
  fi

  run_rg_check \
    "stable mock data/factories must not use dynamic clocks or uncontrolled random values" \
    'Date\.now\(|Math\.random\(|crypto\.randomUUID\(|new Date\(\)' \
    "$MOCK_ROOT/data" "$MOCK_ROOT/factories"

  openapi_binding_lines="$(
    rg -n --glob '*.{ts,tsx}' '@/api/_generated' \
      "$MOCK_ROOT/contracts" "$MOCK_ROOT/data" "$MOCK_ROOT/handlers" 2>/dev/null || true
  )"
  if [[ -z "$openapi_binding_lines" ]]; then
    report_failure \
      "mock mainline must bind to generated OpenAPI types" \
      "Expected src/mocks/contracts, data, or handlers to import '@/api/_generated'."
  fi

  relative_date_lines="$(
    rg -n --glob '*.{ts,tsx}' 'faker\.date\.(recent|soon|past|future)' \
      "$MOCK_ROOT/data" "$MOCK_ROOT/factories" 2>/dev/null \
      | rg -v 'refDate' || true
  )"
  if [[ -n "$relative_date_lines" ]]; then
    report_failure "faker relative dates must pass a fixed refDate" "$relative_date_lines"
  fi
fi

doc_files=(
  "$PROJECT_ROOT/ruoyi-fastapi-frontend/src/mocks/README.md"
  "$PROJECT_ROOT/docs/demo-offline-runtime-scenario-package-runbook.md"
  "$PROJECT_ROOT/docs/specs/README.md"
  "$PROJECT_ROOT/docs/specs/contract-first-single-dataset-mock-platform/module-definition-of-done.md"
  "$PROJECT_ROOT/docs/specs/contract-first-single-dataset-mock-platform/legacy-runtime-retirement-checklist.md"
)

existing_doc_files=()
for file in "${doc_files[@]}"; do
  [[ -f "$file" ]] && existing_doc_files+=("$file")
done

if (( ${#existing_doc_files[@]} > 0 )); then
  doc_keyword_lines="$(
    rg -n -i 'MCP|candidate|promote|active pointer|active/candidate|runtime package writer' \
      "${existing_doc_files[@]}" 2>/dev/null \
      | rg -v 'legacy|paused|legacy/paused|暂停|冻结|历史|旧|退场|不再|不得|禁止|不是|非当前|不作为|已降级|已暂停' \
      || true
  )"
  if [[ -n "$doc_keyword_lines" ]]; then
    report_failure "current mock docs must not describe MCP/candidate/promote as mainline acceptance" "$doc_keyword_lines"
  fi
fi

if [[ -d "$DIST_DEMO_OFFLINE" ]]; then
  if [[ "$require_dist" == true && ! -f "$DIST_DEMO_OFFLINE/index.html" ]]; then
    report_failure \
      "dist-demo-offline build output is incomplete" \
      "Expected $DIST_DEMO_OFFLINE/index.html after yarn build:demo-offline."
  fi

  scan_build_output "$DIST_DEMO_OFFLINE" "dist-demo-offline"
elif [[ "$require_dist" == true ]]; then
  report_failure \
    "dist-demo-offline build output missing" \
    "Run: cd $PROJECT_ROOT/ruoyi-fastapi-frontend && yarn build:demo-offline"
fi

scan_build_output "$DIST_PROD" "dist"

if (( failures > 0 )); then
  printf '\nMock mainline check failed with %d issue(s).\n' "$failures" >&2
  exit 1
fi

echo "Mock mainline checks passed."
