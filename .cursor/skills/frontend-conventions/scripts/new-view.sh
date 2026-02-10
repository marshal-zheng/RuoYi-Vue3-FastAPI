#!/usr/bin/env bash
# Scaffold a CRUD view using frontend-conventions templates.
# Usage:
#   bash .cursor/skills/frontend-conventions/scripts/new-view.sh <module> <entity>
#   bash .cursor/skills/frontend-conventions/scripts/new-view.sh --dry-run <module> <entity>
set -euo pipefail

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
  shift
fi

if [ $# -lt 2 ]; then
  echo "Usage: $0 [--dry-run] <module> <entity>"
  echo "Example: $0 system dept"
  exit 1
fi

MODULE="$1"
ENTITY="$2"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR"
while [ "$ROOT" != "/" ] && [ ! -f "$ROOT/ruoyi-fastapi-frontend/package.json" ]; do
  ROOT="$(dirname "$ROOT")"
done

if [ ! -f "$ROOT/ruoyi-fastapi-frontend/package.json" ]; then
  echo "Cannot locate repository root from $SCRIPT_DIR"
  exit 1
fi

FE_DIR="${ROOT}/ruoyi-fastapi-frontend"
ASSETS_DIR="$(cd "$SCRIPT_DIR/../assets" && pwd)"

python3 - "$FE_DIR" "$ASSETS_DIR" "$MODULE" "$ENTITY" "$DRY_RUN" <<'PY'
import json
import os
import re
import sys
from pathlib import Path

fe_dir = Path(sys.argv[1])
assets_dir = Path(sys.argv[2])
module = sys.argv[3]
entity_raw = sys.argv[4]
dry_run = sys.argv[5] == "1"

entity = entity_raw.strip()
if not entity:
    raise SystemExit("Entity cannot be empty")

parts = [p for p in re.split(r"[-_]", entity) if p]
entity_pascal = "".join(p[:1].upper() + p[1:] for p in parts) or entity[:1].upper() + entity[1:]

replacements = {
    "{{module}}": module,
    "{{entity}}": entity,
    "{{Entity}}": entity_pascal,
}


def render(text: str) -> str:
    out = text
    for key, value in replacements.items():
        out = out.replace(key, value)
    return out


created = []
skipped = []
planned = []


def write_file(path: Path, content: str):
    display = str(path).replace(str(fe_dir) + os.sep, "")
    if path.exists():
        skipped.append(display)
        return
    if dry_run:
        planned.append(display)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(display)


# API file
api_tpl = json.loads((assets_dir / "api-template.json").read_text(encoding="utf-8"))
api_content = render(api_tpl["content"])
api_file = fe_dir / "src" / "api" / module / f"{entity}.ts"
write_file(api_file, api_content)

# View files
view_tpl = json.loads((assets_dir / "view-template.json").read_text(encoding="utf-8"))
view_files = view_tpl.get("files", {})
view_root = fe_dir / "src" / "views" / module / entity
for rel_path, template_content in view_files.items():
    final_rel_path = render(rel_path)
    final_content = render(template_content)
    write_file(view_root / final_rel_path, final_content)

print("")
print("Scaffold summary:")
if dry_run:
    if planned:
        print("  [PLAN]")
        for p in planned:
            print(f"    - {p}")
    else:
        print("  [PLAN] Nothing to create")
else:
    if created:
        print("  [CREATED]")
        for c in created:
            print(f"    - {c}")
    if skipped:
        print("  [SKIPPED]")
        for s in skipped:
            print(f"    - {s}")

print("")
print("Next steps:")
print("  1. Add/verify route and permission key mappings.")
print("  2. Replace placeholder columns, form fields, and API payload types.")
print("  3. Run validate script: bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed")
PY
