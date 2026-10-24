# Remaining real-page QA inventory

- Prior user/role/protocol/profile/session/upload/import flows retain their bounded reports; this run targets unverified workflows and reruns affected ones only.
- System CRUD: config, department, post, menu, dictionary type/data and notice editing. For each: actual page controls, required validation, unique owned creation, detail/readback, edit/cancel/reopen, one persisted update, filtering/clear or scoped export where available, deletion and readback. Include editor 404/retry and delayed-close isolation on at least two remaining editor families.
- Project: live route and all reachable non-simulation controls; create/edit/detail, owned version/configuration, export/import round trip. Distinguish inaccessible duplicate consumers from live navigation; no simulation claims.
- Scheduler: inspect module_task.scheduler_test.job (only prints), own paused job CRUD, detail, invalid input, harmless manual run and scoped log read; do not execute existing jobs.
- Monitor/tools: real online users, operation/login/audit/job logs, server/cache, Swagger/data-monitor/codegen/form-builder routes. Record actual endpoints and rendered state. No global cache/log deletion, other-user logout, existing-job execution or existing-table mutation.
- Viewports: 1440x1000 and 1100x800. Inspect initial form fields and fixed actions, loaded/error/recovered states, list feedback and result dialogs. Wait for transitions to settle before final screenshots; also inspect one transition state.
- Exploratory: duplicate owned name/key conflict and recovery, canceled dirty draft, late/failed detail, filter clear, small viewport, nonexistent record and export parsing.
- Evidence: method/path/status only for network receipts, safe owned fields for readback. Never persist raw credentials/cookies/tickets. Distinguish API probes, UI controls, diagnostics and source/unit checks.
- Cleanup only recorded owned IDs after identity verification; remove owned temporary menu entries last. Log out owned sessions, close browser/API contexts and leave local services running.
