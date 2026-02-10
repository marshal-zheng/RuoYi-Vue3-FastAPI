# Feature Specifications

This directory contains structured specifications for features following a three-phase workflow:

## Structure

Each feature specification lives in its own folder with three core files:

```
specs/
└── feature-name/
    ├── requirements.md  # User stories with EARS acceptance criteria
    ├── design.md        # Technical architecture and diagrams
    └── tasks.md         # Implementation tasks with progress tracking
```

## Workflow

1. **Requirements Phase** - Define user stories and acceptance criteria using EARS notation
   - Format: `WHEN [condition] THE SYSTEM SHALL [behavior]`
   - Focus on what, not how

2. **Design Phase** - Document technical architecture
   - System components and interactions
   - Sequence diagrams for complex flows
   - Data models and API contracts

3. **Implementation Phase** - Break down into discrete tasks
   - Each task is independently testable
   - Track progress with checkboxes
   - Update status as work progresses

## Best Practices

- One spec per feature (not per epic or entire project)
- Keep requirements testable and unambiguous
- Update specs as requirements evolve
- Version control specs alongside code
- Reference specs in commits and PRs

## Examples

Good spec scope:
- `user-authentication/` - Login, signup, password reset
- `product-search/` - Search UI, filters, pagination
- `payment-gateway/` - Stripe integration, webhooks

Too broad:
- `entire-ecommerce-platform/` - Split into multiple specs

Too narrow:
- `add-loading-spinner/` - Not worth a spec, just implement
