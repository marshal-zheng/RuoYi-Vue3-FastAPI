# Layout geometry and resource fixture

This fixture mounts the real business shell and ZXUI components with deterministic
catalog/auth/theme controls and local table data. It exercises a real X6 graph and
the real form builder. It does not access the user's existing browser session.

From `ruoyi-fastapi-frontend`, start the source fixture:

```sh
ZXUI_LAYOUT_REPO=/Users/hqz/Downloads/element-plus yarn vite --config tests/fixtures/layout-regions/vite.config.ts
```

Then run the isolated headless checks:

```sh
node scripts/check-layout-regions.mjs
```

For installed-package verification, use a separate cache and port:

```sh
LAYOUT_TEST_INSTALLED=1 LAYOUT_TEST_PORT=4197 yarn vite --config tests/fixtures/layout-regions/vite.config.ts
LAYOUT_TEST_URL=http://127.0.0.1:4197 LAYOUT_EVIDENCE_DIR=../docs/reports/evidence/2026-10-13-zxui-layout-regions/installed node scripts/check-layout-regions.mjs
```

The runner checks 3 viewport sizes × 4 content kinds × 8 visibility combinations,
plus natural short details, nested regions, sticky summaries/actions, iframe,
copyright space, route overrides, mobile drawer and form properties. It records
layout-owned resources, repeated mount/unmount behavior, a native Element Plus
Table control, idle layout count and 40 visibility updates.

Observer probes retain instances to inspect their registered targets. Connected
targets measure active page resources; detached targets are compared with the
native table control, not presented as a browser garbage-collection measurement.
Timing results are local Chromium diagnostics with these probes enabled, not a
cross-machine or old-shell frame-rate benchmark. Allow the existing route
transition to finish before measuring idle layout work.

To reproduce legacy preferences with the actual business settings store and real
settings panel, start the fixture with the theme adapter stub only:

```sh
LAYOUT_TEST_REAL_SETTINGS=1 LAYOUT_TEST_INSTALLED=1 yarn vite --config tests/fixtures/layout-regions/vite.config.ts
node scripts/check-layout-preferences.mjs
```

This seeds an old enabled Tags-Views choice, verifies one-time migration and
preservation of other preferences, then enables/saves through the actual panel
and reloads to verify the new explicit choice survives. It also checks fresh
storage and the content height in both states. Use a free port via
`LAYOUT_TEST_PORT` and pass its URL through `LAYOUT_TEST_URL` if needed.
