# Historical API and real-page QA inventory

- All 41 historical-only operations require new live-service requests and semantic readback. Real page clicks are recorded separately from API-only alternatives.
- User: create, validation, cancel/reopen, detail/edit, status off/on, reset own target password, assignment, template/download/export and valid import; inspect editor plus import result at two viewports.
- Profile: own nickname/contact update, password update and login, avatar select/crop/upload/display; never change the built-in admin profile/password.
- Role: list/create/edit/status off/on, custom department scope, menus, export, authorized/unassigned users, add, single revoke, batch revoke, user-to-role replacement, delete. Verify grant/readback consistency in both directions.
- Protocol: real routed page, list/filter, create detail/edit, single and batch delete, template/preview/single import/batch import/export and round-trip fields. Add only a temporary owned menu if the existing route is absent.
- Error exploration: invalid/duplicate user/role submit gives one useful failure and no partial write; corrupted protocol workbook and invalid child field are rejected without 500 or writes.
- Visual: initial and post-action states; 1440x1000 and 1100x800; fields, trees, upload controls and primary footer actions remain visible. Dense field tables may scroll inside their own container.
- Cleanup: verify identities then delete only owned records, imported users/protocols, role relationships and temporary menu; revoke owned sessions, remove uploaded own avatar file, retain shared audit trails.
- Preserve existing edits; no commits/pushes; no global cache/log flush, schema migration or simulation workflows.
