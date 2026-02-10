# Documentation Structure

This directory contains all project documentation organized by purpose.

## Directory Structure

```
docs/
├── specs/           # Feature specifications (requirements → design → tasks)
├── codemaps/        # Architecture code maps (auto-generated snapshots)
├── learned/         # Reusable patterns and solutions
├── reports/         # Historical reports 
```

## Directory Purpose

### `/specs` - Feature Specifications
Structured specifications for features following the three-phase workflow:
- `requirements.md` - User stories with EARS notation acceptance criteria
- `design.md` - Technical architecture and sequence diagrams
- `tasks.md` - Discrete implementation tasks with progress tracking

Each feature gets its own folder (e.g., `specs/user-authentication/`).

### `/codemaps` - Architecture Code Maps
Auto-generated snapshots of codebase structure:
- `overview.md` - High-level system architecture
- `backend.md` - Backend module structure
- `frontend.md` - Frontend component hierarchy
- `data.md` - Data models and migrations

Generated via `.cursor/commands/update-codemaps.md`.

### `/learned` - Reusable Patterns
Extracted patterns from problem-solving sessions:
- Error resolution patterns
- Debugging techniques
- Library workarounds
- Project-specific conventions

Created via `.cursor/commands/learn.md`.

### `/reports` - Historical Reports
Archived completion reports, audit summaries, and migration documents.

## Maintenance

- **specs**: Update when requirements change via spec session refinement
- **codemaps**: Regenerate monthly or after major architectural changes
- **learned**: Add new patterns as discovered during development
- **reports**: Archive only, do not modify
