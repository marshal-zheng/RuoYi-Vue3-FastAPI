# Upload and stream QA inventory

- Real user import page: download template, upload a valid workbook with only QA-owned names, submit once, inspect result, read back created users, cancel/failed-import state, and clean the users.
- Real notice editor: open add notice, image toolbar and native file chooser, real backend upload, embedded image loads, save a QA-owned notice and read its persisted HTML, then remove only this notice and uploaded file.
- FileUpload/ImageUpload: globally registered wrappers have no current handwritten route consumer; a labelled temporary browser-mounted fixture uses the actual components and real backend. Exercise valid selection, invalid extension/size, progress/success/failure, removal and unmount cancellation; inspect committed paths and image preview.
- Authentication: verify upload after the original 600-second access lifetime (no policy change), mixed concurrent requests and terminal revocation; distinguish controlled access-key eviction probes from natural wall-clock expiry.
- SSE: actual native EventSource reconnect after access expiry, and no reconnect after logout; unit probes cover stopped/old-source callbacks.
- WebSocket: real browser handshake with fresh tickets, ping/pong, ticket reuse, mismatched path, expiry/revocation and ticket reacquisition through HTTP. Simulation workflows are not migrated or claimed as visually accepted.
- Viewports: 1440x1000 and 1100x800 for relevant dialogs and fixture; ensure file lists, progress/errors, preview and save/cancel controls are visible.
- Evidence omits raw tokens, cookies, query tickets and Authorization headers. Cleanup verifies owned identity/path before deletion; keep application services running.
