data "external_schema" "sqlalchemy" {
  program = [
    "./venv/bin/python",
    "scripts/internal/db_workflow/schema_apply_atlas.py",
    "schema",
  ]
}

env "sqlalchemy" {
  src = data.external_schema.sqlalchemy.url
}
