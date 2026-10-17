# First refresh timeout: independent frontend root-cause audit

Date: 2026-10-17. Scope: read-only production audit and scheduled memory probe. No browser/computer use, actual HTTP writes, source edits, or live environment changes. Inspected installed package and ZXUI source. This review uses the receiving-code-review discipline: evidence before a proposed fix.

## Conclusion

No deterministic frontend lost-invalidation defect was found in the current department command/native query path. Eight scheduled write/invalidation interleavings (four for installed package, four for source helper) all converge to parent + child, including a canceled first response resolved after the second response. A fresh successful query returning an old server snapshot deterministically reproduces the probe symptom: old data remains with `fetchStatus=idle` and `isInvalidated=false`; without a further trigger, a 15-second poll for a new node times out. That is a boundary demonstrated by the controlled memory probe, not proof that this exact server condition occurred in the initial historical run.

The original initial-failure evidence cannot uniquely determine its cause. It lacks per-response statuses, cache node snapshots, query errors/fetch states, and request/response times. Subsequent seven passing real rounds neither reconstruct that history nor rule out a cache race. It is correct to repair a proven backend race if a separate controlled backend probe establishes it, but the report should retain this distinction.

## Static contract and implementation

- Department command writes call `invalidateQueryGroups` after their successful HTTP response. The invalidation promise is intentionally detached from the saved mutation result; UI read failures cannot turn a committed write into a false mutation failure. This is consistent with the product contract.
- The source helper and installed `@zxio/vue-query` helper are equivalent: match the union, await native `cancelQueries`, then native `invalidateQueries` with `refetchType: active`.
- Current real dependency resolution is `@tanstack/vue-query` 5.92.5 with `@tanstack/query-core` 5.90.16, confirmed through `createRequire` rooted at the actual installed Vue Query entry (no nested second query-core copy in this resolution).
- Core `cancelQueries` defaults `revert: true`. `invalidateQueries` marks the matching query stale and delegates to `refetchQueries`; `cancelRefetch` defaults true. A new refetch with defined cached data cancels a pending refetch before replacing it. After canceled old work is resolved late, that canceled promise cannot call setData and overwrite the replacement.
- The real probe awaits cold `fetchQuery` for both observed resources before writing, so each query already has data (including a valid empty array/list). The no-cached-data refetch-sharing exception does not explain this probe.
- Query request signal is forwarded into HTTP with the query-owned marker; there is no extra frontend GET data cache in `@zxio/http` or this request bridge.
- The probe's predicate is child presence in the flat management collection and recursive user tree. Both recorded later modes pass that same predicate. The two create calls are sequential HTTP writes, but correctly do not wait for the first background read; requiring that extra wait would hide the relevant race.

## Exact scheduled-memory verification

Command: `node /tmp/refresh-frontend-memory.cjs` (durable copy beside this report).

Uses real installed `QueryClient` and `QueryObserver`, source or installed invalidation helper, controlled successful read promises, and a model database snapshot taken at each query start. No HTTP, database, Redis or mutation endpoint is used.

| Schedule | Installed | Source | Expected result |
| --- | --- | --- | --- |
| First write refresh settles before second write | pass | pass | parent + child |
| First write refresh pending, second cancels it; old response delivered last | pass | pass | parent + child; one abort |
| Both invalidations issued in same JS turn | pass | pass | parent + child; one abort |
| First cancel wait delayed across second write/refresh | pass | pass | parent + child |
| Latest native request succeeds with a stale server snapshot | reproduced | reproduced | parent only; idle; no invalidated flag |

Machine evidence: `refresh-frontend-memory-results.json`. Probe source: `refresh-frontend-memory.cjs`. SHA-256 of inspected production and probe inputs: `refresh-frontend-audit-inputs.json`.

## What the historical counts prove

The initial failed installed run records 2 POST creates, 3 GET user trees and 5 GET management lists. This is consistent with one cold read plus one read after each create for both resources, followed by the two direct management-list reads used by cleanup. It proves matching requests were initiated, not that the final user-tree or list response was successful, timely, fresh, or accepted. Error/paused query behavior can also preserve the old successful data by design.

The added current timeout diagnostic reads the cache and direct APIs only after timeout, so later failures could distinguish client stale/error from an API response stale at that point, but those direct reads are not a faithful reconstruction of the previous read time or database snapshot. A bounded request/response trace should retain method, owned-marker node identities/counts only, timestamps, success/status, and query state; no token, headers, config object, or real user row data.

## Recommendation to parent

Do not add redundant frontend refresh calls, polling, delays between saves, a custom scheduler, or await all refetches before resolving successful writes. Those changes do not establish server-read correctness and would weaken the existing generic native Query contract. Continue with the independently proven backend cache/transaction ordering investigation, including old reader refill across a write/invalidation. Keep the historical first-run cause marked as inferred unless a preserved matching response trace proves it.

Reference: [TanStack Vue Query cancellation guide](https://tanstack.com/query/latest/docs/framework/vue/guides/query-cancellation) documents consumed AbortSignal cancellation and state reversion. Exact behavior above is verified from the installed 5.90.16 source and executable schedules, rather than assuming current documentation equals installed implementation.
