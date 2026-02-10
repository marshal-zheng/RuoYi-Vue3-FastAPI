#!/usr/bin/env bash
# Frontend validation script.
# Default mode validates only changed files (brownfield-friendly).
# Usage:
#   bash .cursor/skills/frontend-conventions/scripts/validate.sh
#   bash .cursor/skills/frontend-conventions/scripts/validate.sh --full --with-tests
set -euo pipefail

MODE="changed"
RUN_TESTS=0
RUN_LINT=1
RUN_TYPECHECK=0
ERRORS=0
TYPECHECK_EXPLICIT=0
TYPECHECK_DISABLED=0

usage() {
  cat <<'EOF'
Usage: validate.sh [options]

Options:
  --changed        Validate changed files only (default)
  --full           Validate full frontend source tree
  --with-typecheck Run vue-tsc (default on --full, off on --changed)
  --with-tests     Run unit tests (default off)
  --skip-lint      Skip eslint
  --skip-typecheck Skip vue-tsc
  -h, --help       Show this help
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --changed)
      MODE="changed"
      ;;
    --full)
      MODE="full"
      ;;
    --with-typecheck)
      RUN_TYPECHECK=1
      TYPECHECK_EXPLICIT=1
      ;;
    --with-tests)
      RUN_TESTS=1
      ;;
    --skip-lint)
      RUN_LINT=0
      ;;
    --skip-typecheck)
      RUN_TYPECHECK=0
      TYPECHECK_DISABLED=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

if [ "$MODE" = "full" ] && [ "$TYPECHECK_EXPLICIT" -eq 0 ] && [ "$TYPECHECK_DISABLED" -eq 0 ]; then
  RUN_TYPECHECK=1
fi

heading() { printf '\n==> %s\n' "$1"; }
pass()    { printf '  [OK] %s\n' "$1"; }
warn()    { printf '  [WARN] %s\n' "$1"; }
fail()    { printf '  [FAIL] %s\n' "$1"; ERRORS=$((ERRORS + 1)); }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR"
while [ "$ROOT" != "/" ] && [ ! -f "$ROOT/ruoyi-fastapi-frontend/package.json" ]; do
  ROOT="$(dirname "$ROOT")"
done

if [ ! -f "$ROOT/ruoyi-fastapi-frontend/package.json" ]; then
  echo "[FAIL] Cannot locate repository root from $SCRIPT_DIR"
  exit 1
fi

FE_DIR="${ROOT}/ruoyi-fastapi-frontend"
SRC_DIR="${FE_DIR}/src"

collect_changed_files() {
  git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 1
  CHANGED_FILES=()
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    CHANGED_FILES+=("$line")
  done < <(
    {
      git -C "$ROOT" diff --name-only --cached -- ruoyi-fastapi-frontend/src
      git -C "$ROOT" diff --name-only -- ruoyi-fastapi-frontend/src
      git -C "$ROOT" ls-files --others --exclude-standard -- ruoyi-fastapi-frontend/src
    } | awk 'NF' | sort -u
  )
  return 0
}

TARGET_FILES=()
if [ "$MODE" = "changed" ]; then
  if collect_changed_files; then
    for f in "${CHANGED_FILES[@]:-}"; do
      [ -n "$f" ] || continue
      case "$f" in
        *.vue|*.js|*.ts|*.jsx|*.tsx|*.css|*.less|*.scss)
          TARGET_FILES+=("$f")
          ;;
      esac
    done
  else
    warn "Git context not available, falling back to --full mode"
    MODE="full"
  fi
fi

if [ "$MODE" = "full" ]; then
  TARGET_FILES=()
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    TARGET_FILES+=("$line")
  done < <(
    find "$SRC_DIR" -type f \
      \( -name '*.vue' -o -name '*.js' -o -name '*.ts' -o -name '*.jsx' -o -name '*.tsx' -o -name '*.css' -o -name '*.less' -o -name '*.scss' \) \
      | sed "s#^$ROOT/##" \
      | sort
  )
fi

HAS_TARGET_FILES=0
if [ -n "${TARGET_FILES[0]-}" ]; then
  HAS_TARGET_FILES=1
fi

if [ "$HAS_TARGET_FILES" -eq 0 ]; then
  warn "No frontend source files to validate"
fi

is_tracked_file() {
  git -C "$ROOT" ls-files --error-unmatch "$1" >/dev/null 2>&1
}

is_hex_allowlist_file() {
  case "$1" in
    ruoyi-fastapi-frontend/src/assets/styles/tailwind.css|\
    ruoyi-fastapi-frontend/src/assets/styles/theme.module.css|\
    ruoyi-fastapi-frontend/src/assets/styles/design-tokens.css)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_console_allowlist_file() {
  case "$1" in
    ruoyi-fastapi-frontend/src/mocks/*|\
    ruoyi-fastapi-frontend/src/utils/console.ts)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

file_matches_pattern() {
  local file="$1"
  local patch_pattern="$2"
  local full_pattern="$3"
  local abs="$ROOT/$file"

  if [ "$MODE" = "changed" ]; then
    if is_tracked_file "$file"; then
      local patch
      patch="$(
        {
          git -C "$ROOT" diff --cached --unified=0 --no-color -- "$file"
          git -C "$ROOT" diff --unified=0 --no-color -- "$file"
        } || true
      )"
      [ -n "$patch" ] || return 1
      printf '%s\n' "$patch" | rg --pcre2 --quiet "$patch_pattern"
    else
      rg --pcre2 --quiet "$full_pattern" "$abs"
    fi
  else
    rg --pcre2 --quiet "$full_pattern" "$abs"
  fi
}

# 1) Lint
heading "ESLint"
if [ "$RUN_LINT" -eq 1 ]; then
  if [ "$MODE" = "changed" ]; then
    if [ "$HAS_TARGET_FILES" -eq 0 ]; then
      pass "No changed frontend files to lint"
    else
      LINT_FILES=()
      for f in "${TARGET_FILES[@]-}"; do
        [ -n "$f" ] || continue
        case "$f" in
          *.vue|*.js|*.ts|*.jsx|*.tsx)
            LINT_FILES+=("${f#ruoyi-fastapi-frontend/}")
            ;;
        esac
      done
      HAS_LINT_FILES=0
      if [ -n "${LINT_FILES[0]-}" ]; then
        HAS_LINT_FILES=1
      fi
      if [ "$HAS_LINT_FILES" -eq 0 ]; then
        pass "No JS/TS/Vue changed files to lint"
      elif (cd "$FE_DIR" && yarn eslint "${LINT_FILES[@]-}" >/dev/null); then
        pass "Lint passed on changed files"
      else
        fail "Lint failed on changed files (run: cd ruoyi-fastapi-frontend && yarn lint)"
      fi
    fi
  elif (cd "$FE_DIR" && yarn lint:check >/dev/null); then
    pass "Lint passed"
  else
    fail "Lint failed (run: cd ruoyi-fastapi-frontend && yarn lint)"
  fi
else
  warn "Lint skipped"
fi

# 2) Type check
heading "Type Check"
if [ "$RUN_TYPECHECK" -eq 1 ]; then
  if (cd "$FE_DIR" && yarn type-check >/dev/null); then
    pass "Type check passed"
  else
    fail "Type check failed (run: cd ruoyi-fastapi-frontend && yarn type-check)"
  fi
else
  warn "Type check skipped"
fi

# 3) Hex color policy
heading "Color Token Policy"
HEX_VIOLATIONS=()
for file in "${TARGET_FILES[@]-}"; do
  [ -n "$file" ] || continue
  is_hex_allowlist_file "$file" && continue
  if file_matches_pattern "$file" '^\+[^+].*#[0-9a-fA-F]{3,8}\b' '#[0-9a-fA-F]{3,8}\b'; then
    HEX_VIOLATIONS+=("$file")
  fi
done
if [ "${#HEX_VIOLATIONS[@]}" -gt 0 ]; then
  fail "Hex colors detected in non-token files (use Tailwind classes or CSS variables)"
  printf '  Files:\n'
  printf '    - %s\n' "${HEX_VIOLATIONS[@]}" | head -20
else
  pass "No new hex color violations"
fi

# 4) Runtime axios import policy
heading "HTTP Layer Policy"
AXIOS_VIOLATIONS=()
for file in "${TARGET_FILES[@]-}"; do
  [ -n "$file" ] || continue
  case "$file" in
    *.js|*.ts|*.jsx|*.tsx|*.vue)
      if [ "$file" = "ruoyi-fastapi-frontend/src/utils/request.ts" ]; then
        continue
      fi
      if file_matches_pattern "$file" "^\+[^+].*import\\s+(?!type\\b).*from\\s+['\\\"]axios['\\\"]" "^\\s*import\\s+(?!type\\b).*from\\s+['\\\"]axios['\\\"]"; then
        AXIOS_VIOLATIONS+=("$file")
      fi
      ;;
  esac
done
if [ "${#AXIOS_VIOLATIONS[@]}" -gt 0 ]; then
  fail "Runtime axios import detected outside request wrapper"
  printf '  Files:\n'
  printf '    - %s\n' "${AXIOS_VIOLATIONS[@]}"
else
  pass "No runtime axios violations"
fi

# 5) Vue script setup policy
heading "Vue Component Policy"
OPTIONS_VIOLATIONS=()
for file in "${TARGET_FILES[@]-}"; do
  [ -n "$file" ] || continue
  case "$file" in
    *.vue)
      if file_matches_pattern "$file" '^\+[^+].*export\s+default\s*\{' 'export\s+default\s*\{'; then
        OPTIONS_VIOLATIONS+=("$file")
      fi
      ;;
  esac
done
if [ "${#OPTIONS_VIOLATIONS[@]}" -gt 0 ]; then
  fail "Options API usage detected in changed Vue files (prefer <script setup>)"
  printf '  Files:\n'
  printf '    - %s\n' "${OPTIONS_VIOLATIONS[@]}"
else
  pass "No Options API regressions"
fi

# 6) Console usage policy
heading "Console Usage Policy"
CONSOLE_VIOLATIONS=()
for file in "${TARGET_FILES[@]-}"; do
  [ -n "$file" ] || continue
  case "$file" in
    *.js|*.ts|*.jsx|*.tsx|*.vue)
      is_console_allowlist_file "$file" && continue
      if file_matches_pattern "$file" '^\+[^+].*console\.(log|warn|error)\(' 'console\.(log|warn|error)\('; then
        CONSOLE_VIOLATIONS+=("$file")
      fi
      ;;
  esac
done
if [ "${#CONSOLE_VIOLATIONS[@]}" -gt 0 ]; then
  fail "console.log/warn/error added in business code"
  printf '  Files:\n'
  printf '    - %s\n' "${CONSOLE_VIOLATIONS[@]}"
else
  pass "No new console usage violations"
fi

# 7) Unit tests (optional)
heading "Unit Tests"
if [ "$RUN_TESTS" -eq 1 ]; then
  if (cd "$FE_DIR" && yarn test:run >/dev/null); then
    pass "Tests passed"
  else
    fail "Tests failed (run: cd ruoyi-fastapi-frontend && yarn test:run)"
  fi
else
  warn "Tests skipped (use --with-tests to enable)"
fi

echo ""
if [ "$ERRORS" -gt 0 ]; then
  printf '[FAIL] %d check(s) failed\n' "$ERRORS"
  exit 1
fi
printf '[OK] All checks passed\n'
