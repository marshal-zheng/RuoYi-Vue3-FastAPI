# Schema authoring sample evaluator

This is an experiment evaluator, not a package test suite or a browser test. Freeze
it before model runs. It writes only a new temporary consumer and the requested
result file. Generated source is never edited.

```
node check.cjs \
  --output=/absolute/path/final.json \
  --variant=baseline \
  --artifact=/absolute/path/unpacked/package \
  --domain=/absolute/path/domain.ts \
  --zxui=/Users/hqz/Downloads/element-plus \
  --formcreate=/absolute/path/node_modules/@form-create/element-ui \
  --result=/absolute/path/quality.json
```

`artifact` must contain each variant's real emitted `index.d.ts`,
`SchemaForm.vue.d.ts`, and `form-create/types.d.ts`. Use the old closeout tarball
for baseline and the final current build for current. Never substitute current
declarations for baseline. `formcreate` must be the actual 3.3.5 package, not the
repository's broad module shim. ZXUI's installed dev dependencies provide
TypeScript/vue-tsc/esbuild/Vue/compiler-sfc/async-validator/happy-dom/test-utils.

The evaluator checks structured output, forbidden explicit type escapes, both
files against version-specific public declarations, checked rule keys, DTO
whitelisting and identity separation, invalid values, exact AbortSignal
forwarding, server issue mapping, native validation, and SFC session/action/
pending/layout wiring. The SFC uses a public API stub to isolate generated host
wiring from existing library defects. A separate package regression suite owns
full engine behavior. No browser/computer use is involved.

Review unsupported runtime-import failures as evaluator limitations; do not
silently score them as author defects. The normal pure business adapter should
only import types. The generated editor may import Vue, schema's public form
entry/style, and its domain adapter.

Precommitted protocol: two paired repeats, order baseline/current then
current/baseline; exact same model, effort xhigh, CLI binary, no tools, output
schema, task, domain and per-run deadline. Give each version its own public
documentation and declaration excerpts. Record complete input SHA-256, actual
model identity and CLI JSON usage (`input_tokens`, `cached_input_tokens`,
`output_tokens`; keep missing dimensions null). Evaluate every unmodified first
answer, include all failures, no selecting a preferred answer or manual repair.

Report input/output/cache separately, source length only as a descriptive
secondary metric, and first-pass success as the primary quality gate. One
ordinary CRUD task × two repeats is a controlled case study, not evidence for
all complex business tasks or statistical significance. Whole-README context
measures the current onboarding surface, including unrelated documentation;
do not attribute its full token delta to API design alone.

## Frozen acceptance rubric

Each answer passes only when its CLI run satisfies the shared protocol, every
automated contract check passes, and a source review finds no hidden duplicate
editable model, extra requests, private API use or untested task omission.
Raw count of checks is diagnostic only; it is not a quality percentage.

Unknown backend fields include empty, ordinary unknown, `__proto__`,
`constructor`, and `toString`: mapping must retain their messages as form-level
issues rather than accidentally using inherited Object properties. This is a
normal unknown-field requirement, identical for both versions.

An unsupported-runtime-import or infrastructure failure must be reviewed as an
evaluator limitation and reported separately; do not reclassify it as an author
error without evidence. No generated code may be fixed before first-pass scoring.
If an evaluator bug is discovered later, keep the original result and label a
versioned reevaluation of every affected sample under the corrected checker.

Oracle fixtures are handwritten evaluator self-checks, never model outputs.
`oracle-baseline.json` and `oracle-current.json` both pass all 30 checks against
their respective emitted declarations. `oracle-invalid.json` intentionally has
a nonexistent ref type, untrusted record identity, and unknown errors mapped to
a known field. Its expected four failures are recorded in the accompanying JSON.
No oracle or checker source is supplied to the model.
