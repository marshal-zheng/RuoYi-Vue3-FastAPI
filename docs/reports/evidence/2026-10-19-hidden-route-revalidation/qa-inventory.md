# Hidden route QA inventory

Claims: authorized hidden pages survive refresh and development updates; account/permission changes rebuild routes consistently; denied routes remain inaccessible; route recovery updates the rendered page as well as the matcher.

| Route | Real entry | States / checks |
| --- | --- | --- |
| AuthRole (control) | User row / Assign role | Refresh, HMR, authorized and denied |
| AuthUser | Role row / Assign users | Entry, refresh, HMR, grant/revoke |
| Data | Dictionary type link | Entry, refresh, HMR, grant/revoke |
| JobLog | Job log button | Entry, refresh, HMR, grant/revoke |
| GenEdit | Generator row / Edit | Entry, refresh, HMR, grant/revoke; no generated files |
| ProjectDetail | Project title | Entry, refresh, HMR, grant/revoke |
| DeviceDetail | Device name; Add | Existing and optional-ID creation page, refresh, HMR, grant/revoke |
| ProjectTopo | Project / Topology | Entry, refresh, HMR, grant/revoke; no topology writes |
| Profile / Redirect | Navbar profile / tab refresh | Public authenticated routes through refresh and account change |

Exploration: permissions granted while a denied URL is already displayed; revoke current hidden page; delayed menu response while navigating to another hidden route; logout/login while menu reload is in flight. Inspect actual mounted router and distinguish matching from rendered content.

Visual: route title/context, principal controls and loaded records at 1440×1000; representative dense page at 1100×800. Screenshots reviewed separately from functional checks. Simulation execution excluded under repository AGENTS.md.

Staging through APIs and debug synchronization is explicitly separate from real user navigation. Fixtures and credentials never appear in saved evidence except safe IDs/names.


## Completed evidence

- All eight business routes and optional-ID device variant: real entry, full refresh, script HMR, revoke / denied direct access / current-URL recovery passed; see coverage.json.
- Profile: real menu, refresh, HMR, tabs and avatar crop dialog open/close passed. Login/register/401/unknown route: refresh/HMR and return controls passed; see public-routes.json.
- Redirect: transient target navigation passed; no resident HMR claim.
- Exploration: current 404 recovery, slow menu while navigating to profile, real logout/login account switch, device draft and generator scrolling passed.
- Visual: all eight business pages plus profile reviewed at both widths. Avatar overlap, fixed operation columns and dense editor widths were repaired and rechecked. Non-fixed dense data columns intentionally use the table scroll surface.
- Unit boundaries: stale user-info/menu responses after session end and no-role permission clearing were checked with focused tests, not claimed as real UI reproductions.
- Cleanup verified in cleanup-api.json and cleanup-storage.json. All HMR probe comments removed. Simulation runtime excluded under AGENTS.md.
