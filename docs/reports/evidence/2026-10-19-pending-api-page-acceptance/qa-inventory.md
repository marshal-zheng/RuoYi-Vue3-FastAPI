# Pending acceptance QA inventory

- API: all 35 previously unexecuted operations, preserving expected errors as contract checks. Use new owned identities, records and generator tables. Shared destructive operations require a private database/Redis fixture and are reported separately.
- Server dashboard: edit, save, reload, reset to initial layout; inspect toolbar and post-save state at 1440x1000 and 1100x800.
- Generator: create owned table, import another owned table, edit metadata, synchronize only owned schema, preview/download code, delete owned metadata. Inspect editor tabs and download content.
- Logs: create owned traces; filter, inspect and delete only those IDs. Unlock an owned account. Force offline only an owned target.
- Cache: clear own exact key and namespace; preserve adjacent similarly named keys. No shared all-cache click.
- Error exploration: stale dashboard revision rejects overwrite; malformed generator SQL and empty IDs produce useful 4xx.
- Visual evidence: dashboard persisted/reset, generator editor and filtered log controls; inspect readable fields and viewport fit.
- No commit/push; preserve all prior source bytes except demonstrated scoped fixes.
