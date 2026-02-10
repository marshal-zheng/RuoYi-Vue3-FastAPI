#!/usr/bin/env bash
# Backend validation script.
# Default mode validates changed backend Python files only.
# Usage:
#   bash .cursor/skills/backend-conventions/scripts/validate.sh
#   bash .cursor/skills/backend-conventions/scripts/validate.sh --full --with-mypy --with-tests
set -euo pipefail

MODE="changed"
RUN_TESTS=0
RUN_MYPY=0
RUN_RUFF=1
RUN_FORMAT=1
MYPY_EXPLICIT=0
MYPY_DISABLED=0
ERRORS=0

usage() {
  cat <<'USAGE'
Usage: validate.sh [options]

Options:
  --changed      Validate changed files only (default)
  --full         Validate full backend Python source tree
  --with-tests   Run pytest
  --with-mypy    Run mypy
  --skip-mypy    Skip mypy
  --skip-ruff    Skip ruff lint
  --skip-format  Skip ruff format check
  -h, --help     Show this help
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --changed)
      MODE="changed"
      ;;
    --full)
      MODE="full"
      ;;
    --with-tests)
      RUN_TESTS=1
      ;;
    --with-mypy)
      RUN_MYPY=1
      MYPY_EXPLICIT=1
      ;;
    --skip-mypy)
      RUN_MYPY=0
      MYPY_DISABLED=1
      ;;
    --skip-ruff)
      RUN_RUFF=0
      ;;
    --skip-format)
      RUN_FORMAT=0
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

if [ "$MODE" = "full" ] && [ "$MYPY_EXPLICIT" -eq 0 ] && [ "$MYPY_DISABLED" -eq 0 ]; then
  RUN_MYPY=1
fi

heading() { printf '\n==> %s\n' "$1"; }
pass()    { printf '  [OK] %s\n' "$1"; }
warn()    { printf '  [WARN] %s\n' "$1"; }
fail()    { printf '  [FAIL] %s\n' "$1"; ERRORS=$((ERRORS + 1)); }
have_cmd() { command -v "$1" >/dev/null 2>&1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR"
while [ "$ROOT" != "/" ] && [ ! -f "$ROOT/ruoyi-fastapi-backend/pyproject.toml" ]; do
  ROOT="$(dirname "$ROOT")"
done

if [ ! -f "$ROOT/ruoyi-fastapi-backend/pyproject.toml" ]; then
  echo "[FAIL] Cannot locate repository root from $SCRIPT_DIR"
  exit 1
fi

BE_DIR="${ROOT}/ruoyi-fastapi-backend"

collect_changed_files() {
  git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 1
  CHANGED_FILES=()
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    CHANGED_FILES+=("$line")
  done < <(
    {
      git -C "$ROOT" diff --name-only --cached -- ruoyi-fastapi-backend
      git -C "$ROOT" diff --name-only -- ruoyi-fastapi-backend
      git -C "$ROOT" ls-files --others --exclude-standard -- ruoyi-fastapi-backend
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
        *.py)
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
    find "$BE_DIR" \
      \( -path "$BE_DIR/venv" -o -path "$BE_DIR/htmlcov" -o -path "$BE_DIR/__pycache__" -o -path "$BE_DIR/.pytest_cache" \) -prune -o \
      -type f -name '*.py' -print \
      | sed "s#^$ROOT/##" \
      | sort
  )
fi

HAS_TARGET_FILES=0
if [ -n "${TARGET_FILES[0]-}" ]; then
  HAS_TARGET_FILES=1
fi

if [ "$HAS_TARGET_FILES" -eq 0 ]; then
  warn "No backend Python files to validate"
fi

is_tracked_file() {
  git -C "$ROOT" ls-files --error-unmatch "$1" >/dev/null 2>&1
}

file_has_new_pattern() {
  local file="$1"
  local patch_pattern="$2"
  local full_pattern="$3"
  local abs="$ROOT/$file"

  if is_tracked_file "$file"; then
    local patch
    patch="$({
      git -C "$ROOT" diff --cached --unified=0 --no-color -- "$file"
      git -C "$ROOT" diff --unified=0 --no-color -- "$file"
    } || true)"
    [ -n "$patch" ] || return 1
    printf '%s\n' "$patch" | rg --pcre2 --quiet "$patch_pattern"
  else
    rg --pcre2 --quiet "$full_pattern" "$abs"
  fi
}

# 1) Ruff lint
heading "Ruff Lint"
if [ "$RUN_RUFF" -eq 1 ]; then
  if ! have_cmd ruff; then
    warn "ruff not found, skipping lint"
  elif [ "$HAS_TARGET_FILES" -eq 0 ]; then
    pass "No backend Python files to lint"
  else
    LINT_FILES=()
    for f in "${TARGET_FILES[@]:-}"; do
      [ -n "$f" ] || continue
      LINT_FILES+=("${f#ruoyi-fastapi-backend/}")
    done

    if (cd "$BE_DIR" && ruff check "${LINT_FILES[@]}"); then
      pass "Ruff lint passed"
    else
      fail "Ruff lint failed"
    fi
  fi
else
  warn "Ruff lint skipped"
fi

# 2) Ruff format check
heading "Ruff Format"
if [ "$RUN_FORMAT" -eq 1 ]; then
  if ! have_cmd ruff; then
    warn "ruff not found, skipping format check"
  elif [ "$HAS_TARGET_FILES" -eq 0 ]; then
    pass "No backend Python files to format-check"
  else
    FMT_FILES=()
    for f in "${TARGET_FILES[@]:-}"; do
      [ -n "$f" ] || continue
      FMT_FILES+=("${f#ruoyi-fastapi-backend/}")
    done

    if (cd "$BE_DIR" && ruff format --check "${FMT_FILES[@]}"); then
      pass "Ruff format check passed"
    else
      fail "Ruff format check failed"
    fi
  fi
else
  warn "Ruff format check skipped"
fi

# 3) Mypy
heading "Mypy"
if [ "$RUN_MYPY" -eq 1 ]; then
  if ! have_cmd mypy; then
    warn "mypy not found, skipping"
  elif [ "$MODE" = "full" ]; then
    if (
      cd "$BE_DIR" && \
      mypy module_admin config utils exceptions middlewares module_generator module_task sub_applications server.py app.py
    ); then
      pass "Mypy passed (full targets)"
    else
      fail "Mypy failed"
    fi
  elif [ "$HAS_TARGET_FILES" -eq 0 ]; then
    pass "No backend Python files to type-check"
  else
    MYPY_FILES=()
    for f in "${TARGET_FILES[@]:-}"; do
      [ -n "$f" ] || continue
      case "$f" in
        ruoyi-fastapi-backend/tests/*|ruoyi-fastapi-backend/alembic/*)
          continue
          ;;
      esac
      MYPY_FILES+=("${f#ruoyi-fastapi-backend/}")
    done

    if [ -z "${MYPY_FILES[0]-}" ]; then
      pass "No changed mypy targets"
    elif (cd "$BE_DIR" && mypy "${MYPY_FILES[@]}"); then
      pass "Mypy passed (changed targets)"
    else
      fail "Mypy failed on changed targets"
    fi
  fi
else
  warn "Mypy skipped"
fi

# 4) Tests
heading "Pytest"
if [ "$RUN_TESTS" -eq 1 ]; then
  if ! have_cmd pytest; then
    warn "pytest not found, skipping"
  elif [ "$MODE" = "changed" ]; then
    CHANGED_TESTS=()
    for f in "${TARGET_FILES[@]:-}"; do
      [ -n "$f" ] || continue
      case "$f" in
        ruoyi-fastapi-backend/tests/test_*.py|ruoyi-fastapi-backend/tests/*_test.py|ruoyi-fastapi-backend/tests/*/test_*.py|ruoyi-fastapi-backend/tests/*/*_test.py)
          CHANGED_TESTS+=("${f#ruoyi-fastapi-backend/}")
          ;;
      esac
    done

    if [ -n "${CHANGED_TESTS[0]-}" ]; then
      if (cd "$BE_DIR" && pytest -q "${CHANGED_TESTS[@]}"); then
        pass "Pytest passed on changed tests"
      else
        fail "Pytest failed on changed tests"
      fi
    elif (cd "$BE_DIR" && pytest -q); then
      pass "Pytest passed"
    else
      fail "Pytest failed"
    fi
  elif (cd "$BE_DIR" && pytest -q); then
    pass "Pytest passed"
  else
    fail "Pytest failed"
  fi
else
  warn "Pytest skipped"
fi

# 5) Guardrails
heading "Guardrails"
EVAL_EXEC_VIOLATIONS=()
PRINT_VIOLATIONS=()
CONTROLLER_SQL_VIOLATIONS=()
BROAD_EXCEPT_WARNINGS=()

for file in "${TARGET_FILES[@]:-}"; do
  [ -n "$file" ] || continue

  if file_has_new_pattern "$file" '^\+[^+].*\b(eval|exec)\s*\(' '\b(eval|exec)\s*\('; then
    EVAL_EXEC_VIOLATIONS+=("$file")
  fi

  if file_has_new_pattern "$file" '^\+[^+].*\bprint\s*\(' '\bprint\s*\('; then
    PRINT_VIOLATIONS+=("$file")
  fi

  case "$file" in
    ruoyi-fastapi-backend/module_admin/controller/*.py)
      if file_has_new_pattern "$file" '^\+[^+].*query_db\.execute\(' 'query_db\.execute\('; then
        CONTROLLER_SQL_VIOLATIONS+=("$file")
      fi
      ;;
  esac

  if file_has_new_pattern "$file" '^\+[^+].*except\s+Exception(\s+as\s+\w+)?\s*:' 'except\s+Exception(\s+as\s+\w+)?\s*:'; then
    BROAD_EXCEPT_WARNINGS+=("$file")
  fi
done

if [ "${#EVAL_EXEC_VIOLATIONS[@]}" -gt 0 ]; then
  fail "New eval/exec usage detected"
  printf '  Files:\n'
  printf '    - %s\n' "${EVAL_EXEC_VIOLATIONS[@]}"
else
  pass "No new eval/exec usage"
fi

if [ "${#PRINT_VIOLATIONS[@]}" -gt 0 ]; then
  fail "New print() usage detected"
  printf '  Files:\n'
  printf '    - %s\n' "${PRINT_VIOLATIONS[@]}"
else
  pass "No new print() usage"
fi

if [ "${#CONTROLLER_SQL_VIOLATIONS[@]}" -gt 0 ]; then
  fail "New query_db.execute(...) found in controller files"
  printf '  Files:\n'
  printf '    - %s\n' "${CONTROLLER_SQL_VIOLATIONS[@]}"
else
  pass "No new direct SQL execution in controllers"
fi

if [ "${#BROAD_EXCEPT_WARNINGS[@]}" -gt 0 ]; then
  warn "Broad 'except Exception' added; verify re-raise and message hygiene"
  printf '  Files:\n'
  printf '    - %s\n' "${BROAD_EXCEPT_WARNINGS[@]}"
else
  pass "No new broad exception blocks"
fi

# Final status
if [ "$ERRORS" -gt 0 ]; then
  printf '\nValidation failed with %d error(s).\n' "$ERRORS"
  exit 1
fi

printf '\nValidation passed.\n'
