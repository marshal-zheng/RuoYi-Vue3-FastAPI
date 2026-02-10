# Architecture Code Maps

Auto-generated snapshots of the codebase structure. These maps provide a high-level overview without implementation details.

## Files

- `overview.md` - System architecture, entry points, deployment setup
- `backend.md` - Backend modules: controllers, services, repositories, DAOs, entities
- `frontend.md` - Frontend structure: views, components, stores, composables
- `data.md` - Data models, migrations, seed data

## Generation

Run `.cursor/commands/update-codemaps.md` to regenerate these maps.

Maps are automatically:
- Diffed against previous versions
- Timestamped with freshness date
- Approved before overwriting if changes > 30%

## When to Regenerate

- Monthly (for active projects)
- After major architectural changes
- Before onboarding new team members
- When planning significant refactors

## Purpose

Code maps help with:
- Onboarding new developers
- Planning refactoring efforts
- Understanding cross-module dependencies
- Communicating architecture to non-technical stakeholders

**Note**: These are snapshots, not single sources of truth. The actual code is the source of truth.
