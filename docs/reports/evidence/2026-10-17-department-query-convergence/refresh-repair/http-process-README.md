# Explicit local department stale-fill A/B probe

This is temporary verification instrumentation retained in Git metadata, not a product feature or permanent test framework. It creates and deletes only unique owned `codex_dept_refresh_<4 hex>_{parent,child}` departments through normal APIs. It uses real source FastAPI, MySQL and Redis. No product route, permission, config or source file is changed. No computer use or UI rendering is involved.

`backend_runner.py` wraps the source app in a local ContextVar header scope, wraps the true `DeptRepository.find_all_for_tree` so it pauses after the actual SQL result, and accepts ARM/WAIT_LOADED/RELEASE through an owned local Unix socket. It redirects only QueryCache initialization to an isolated owned Redis namespace, leaving security/session paths unchanged. No mocked rows or fake HTTP are used. `http_schedule.py` performs real login, creates parent, starts the controlled old tree GET, waits for its SQL-result event, creates child, verifies a separate SQL connection sees both committed owned rows, releases old GET, then checks a fresh independent GET. There is no probabilistic sleep.

The original and fixed A/B use the same runner and schedule bytes. The original imports source DeptService untouched. The fixed re-executes the source-preserving cache-removal candidate into the DeptService module before importing the source server/container, keeping the source's existing dirty domain rules. All related byte hashes, process IDs, command templates and environment variable **names only** are in `runtime-inputs.json`.

Observed original: old GET 200 omits child; independent GET 200 still omits child, with zero repository calls and two owned Redis department cache keys. Observed fixed: old GET may still legitimately return its earlier snapshot; independent GET 200 includes child, makes one repository call and leaves zero department result-cache keys. In both cases the independent SQL check after child POST 201 saw exactly two owned active rows. Both schedules deleted their two owned records, confirmed absence through normal API and independent SQL, logged out their own session and cleared only their own Redis namespace.

Normal existing frontend real-API probes then passed once in source mode and once in installed/local-package mode against the fixed overlay backend. Each created/deleted two owned `codex_dept_query_...` records and confirmed absence. An initial extra custom trace header in the jsdom frontend probe was rejected by existing CORS preflight before login or DB writes; that temporary harness edit was completely reverted, and its failure artifacts remain separately named `frontend-source-trace-cors-failure.*`. The successful frontend runs used the existing unchanged opt-in harness with no additional header.

Both task-owned backend processes were stopped, port 8088 was closed, owned socket files were removed after verifying those PIDs absent, and shared MySQL/Redis containers stayed running. The frontend records prove service/query integration, not browser acceptance. A final standard source backend without overlay is still needed after actual source delivery.

Reproduction command templates, run from the source backend with port 8088 free (credentials supplied only in environment, never saved):

```sh
./venv/bin/python <metadata>/refresh-http-probe/backend_runner.py \
  --backend-root /Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-backend \
  --control /Users/hqz/dev/RuoYi-Vue3-FastAPI/.git/<owned-short-socket> \
  --namespace codex_dept_refresh_<unique> \
  [--service-overlay <metadata>/DeptService-source-preserved-fixed.py]

CODEX_DEPT_QUERY_WRITE=1 ./venv/bin/python <metadata>/refresh-http-probe/http_schedule.py \
  --control /Users/hqz/dev/RuoYi-Vue3-FastAPI/.git/<owned-short-socket> \
  --output <owned-evidence-json> --expect stale|fresh
```

Set `CODEX_DEPT_PASSWORD` in the process environment and optionally `CODEX_DEPT_USERNAME`. Do not put credentials into the script, evidence or command transcript. Use a fresh namespace and socket; never use product `query_cache` namespace for this probe. After verification, stop only the spawned runner PID and remove only its own stale socket. Do not restart shared services.

The eight historical runs remain untouched. Since the very first failing run did not save per-query response snapshots, this controlled A/B establishes and fixes a concrete causal server defect capable of that failure class; it cannot uniquely reconstruct that historical run.
