# Public field and attachment review evidence

## InputNumber: verified defect, still open

`input-number-aria-ssr.mjs` renders the actually installed Element Plus 2.13.0 with Vue SSR. `input-number-aria-ssr-result.json` is its freshly captured output. It asserts that `aria-invalid` and `aria-describedby` exist on the root wrapper but are absent from the real input. This is a proven attribute-routing defect, not an unverified suspicion. Browser and screen-reader experience were not tested.

The ZXUI wrapper forwards `$attrs` to `ElInputNumber` in `packages/components/input-number/src/input-number-core.vue:8`. The dependency only explicitly forwards `ariaLabel`, id/name and selected native props to its inner `ElInput`; its current public props do not include `inputAttrs`, `ariaDescribedby` or `ariaInvalid`. Slots are prefix/suffix/control icons, and exposed methods are focus/blur. Therefore the recipe has no existing public input-attribute route. MeasurementRows passes these attributes at `pilot/inspection/MeasurementRows.vue:123`; no recipe DOM patch or number-stepper rewrite was made.

Reproduce:

```sh
node /Users/hqz/dev/RuoYi-Vue3-FastAPI/docs/reports/evidence/schema-enterprise-review-2026-10-20/input-number-aria-ssr.mjs
```

## Attachment cancellation: verified and fixed

- `attachment-cancel-before-probe.ts` is the original minimal probe. It compiles the actual AttachmentField SFC and uses a Vue memory renderer with a stub upload transport. The injected upload Promise ignores AbortSignal.
- `attachment-cancel-before-probe-result.json` preserves its actual pre-fix output: both explicit removal and model replacement aborted the signal but retained pending/blocking.
- `attachment-regression-red.txt` preserves the actual pre-fix Vitest failure from 09:40:40 on 2026-10-20. It is explicitly historical, not a fabricated current red run.
- `attachment-regression-case.ts.txt` snapshots the focused regression added to the existing pilot test file. It covers late success/failure, same-UID replacement, immediate release of blocking and accepted-value replacement.
- `AttachmentField.fixed.vue` snapshots the fixed recipe: cancellation retires the operation immediately; callbacks verify request identity; the public upload abort method also retires Element Plus request records.
- `attachment-regression-green.txt` is fresh output from the focused three-chain run after the fix. The new race case stubs only the upload transport; the existing full editing/upload/save and in-flight-reset cases mount the real FormCreate and ZXUI components under the existing pilot simulated-DOM setup.

The historical probe uses the current source path. Its old failing-behavior assertions are expected to fail against the fixed source; no isolated full pre-fix source checkout was reconstructed. The executable regression in the current pilot is the supported recheck.

Recheck command (working directory `/Users/hqz/Downloads/element-plus`, reuses existing isolated dependencies):

```sh
ZX_SCHEMA_FORM_DEPS=/var/folders/80/8sfxkvmx2l755p0cgcrkv3740000gn/T/zxui-inspection-pilot-0ib4sQ ./node_modules/.bin/vitest run --config /Users/hqz/Downloads/element-plus/docs/research/schema-form-pilot/pilot/vite.config.mts --workspace /Users/hqz/Downloads/element-plus/docs/research/schema-form-pilot/pilot/vitest.workspace.mts -t 'attachment|edits the whole form'
```

No computer use, browser automation, external upload, server write, commit or product-source change was performed while collecting this evidence.
