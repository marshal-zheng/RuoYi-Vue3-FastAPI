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

## Demo Offline Semantic Data Platform

`demo-offline` semantic data platform specs use
[`demo-offline-semantic-data-platform`](./demo-offline-semantic-data-platform/) as the
architecture-governance baseline. Spec 0 is documentation-and-governance-only: it fixes
shared terminology, sequencing, compatibility boundaries, quality gates, and cross-spec
rules; it does not implement MCP v2, runtime loader changes, DOMC registry, Scenario Graph,
Generator Recipes, Vue pages, MSW handlers, service/repository changes, IndexedDB schema,
backend APIs, or production-mode behavior.

The approved follow-up split is intentionally lightweight and should remain here rather
than in a separate roadmap document:

| Spec | Suggested directory | Scope |
| --- | --- | --- |
| Spec A | `demo-offline-semantic-blueprint-generation` | First implementation spec; solve visible data homogenization with Business Blueprint, seed-aware generation, DiversityValidator, SemanticCoverageValidator, and the historical P0 runtime package baseline. |
| Spec B | `demo-offline-runtime-package-v2-manifest-slices` | Hard-cut offline-static runtime packages to v2 pointer, manifest, slices, release directories, hash checks, pointer fallback, and import dry-run without bundling a full DOMC registry. |
| Spec C | `demo-offline-domc-registry-and-generator-adapters` | Add DOMC registry, module contracts, generator adapters, and missing-DOMC blockers without redefining the v2 runtime package format. |
| Spec D | `demo-offline-scenario-graph-and-recipes` | Add Scenario Graph, Generator Recipes, low-materialization strategy, and recipe expansion checks without blocking Spec A's short-term semantic quality gains. |

After Spec 0, the recommended next action is to create the
`demo-offline-semantic-blueprint-generation` requirements. Do not jump directly into a v2
manifest/slices implementation before Spec A has been specified and approved.

The existing [`demo-offline-runtime-scenario-package`](./demo-offline-runtime-scenario-package/)
spec remains the historical P0 build-after runtime JSON package baseline for v1
`active.json`, `previous.json`, contract fingerprinting, IndexedDB import dry-run, and
active/previous/default fallback behavior. The current
[`demo-offline-runtime-package-v2-manifest-slices`](./demo-offline-runtime-package-v2-manifest-slices/)
spec records the approved compatibility exception: new demo-offline offline-static builds and
MCP tools are v2-only, with no v1 fallback and no v1 migration promise.

Follow-up semantic specs must reference `demo-offline-semantic-data-platform` and declare
`parentSpec`, `platformLayer`, `upstreamDependencies`, `nonGoals`, and the new or strengthened
`qualityGates` in their introduction or Clarifications. If a follow-up spec changes an
approved Spec 0 boundary, it must first revise Spec 0 or record an explicit compatibility
exception. Follow-up tasks must label their category, such as documentation governance,
MCP generation, runtime loader, contract/schema, validator, repository/importer, or test matrix.

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
