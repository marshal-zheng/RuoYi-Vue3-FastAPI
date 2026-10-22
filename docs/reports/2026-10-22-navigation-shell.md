# Header and Sidebar Navigation Review — 2026-10-22

Status: implemented and verified in the real source-linked local business. No commit or publication.

## Ownership and result

This is a business application-shell change. ZXUI has no matching application-shell abstraction, and the inspected problems were in business layout/composition. Existing ZXUI semantic surfaces and theme colours remain authoritative; no core `--zx-*` or `--el-*` assignments were added. Theme packages and ZXUI source were not changed by this task.

The single brand/collapse band now belongs to the full-height sidebar, aligned with the 56px content header. Desktop widths are 250px expanded and 64px collapsed. Menu rows are 44px with 4px gaps, right-side 6px corners and a 3px selected marker. Root icons and nested text/guides clarify hierarchy. Top-right user/theme controls remain; no sidebar footer user area was introduced. Long sidebar brand text truncates deliberately and retains the full title hint. Login keeps its heading and wraps on narrow screens.

Routes, permissions, hidden/alwaysShow, external/query handling and activeMenu remain on the existing paths. The page action hierarchy from the previous task is retained.

## Mechanisms and findings resolved

- Reused the existing [Element Plus Drawer](https://element-plus.org/en-US/component/drawer) for the mobile modal navigation, focus containment and dismissal. The application focuses its navigation control after opening and restores the launcher after closing, including header-hidden recovery. This replaced the manual backdrop and eliminated keyboard access to background controls while open.
- Reused [ElMenu horizontal ellipsis](https://element-plus.org/en-US/component/menu.html) for TopNav. At 1024px the prior body-width estimate clipped the last entry; the menu now measures its real container and exposes overflow entries, with an accessible “更多菜单” name.
- Installed ElMenu clears open groups on collapse but does not restore the active path on expansion. The business menu switches rail/expanded keys so native defaultActive initialization reveals the current leaf. This avoids duplicating route ancestry or relying on internal component state; manually opened groups already had no preservation guarantee across collapse.
- Removed conflicting 54px rail rules and unused sidebar/logo aliases instead of adding another override layer.

## QA inventory and results

| Claim / control | Functional check | Visual result / evidence |
| --- | --- | --- |
| Aligned brand/header | Single expanded brand; full title hint; fold/expand via Enter and Space | Header 56px, brand 56px; sidebar 250px, rail 64px |
| Clear menu hierarchy | User/role and third-level log routing; current route visible after expansion | 44px rows, 4px gaps, continuous guide, 3px marker, 6px right corners |
| Rail popups | Select role and third-level operation log from teleported menus | Collapsed parent highlight and readable nested popup |
| Top-right user/theme | User menu click and profile navigation; theme/mode round trip | Default light and army-pine dark reviewed; user absent from sidebar |
| Mobile keyboard | Tab and Shift+Tab stay in drawer; Escape closes; menu/outside click return focus | Drawer fits 390px viewport; explicit focus ring; closed overlay removed |
| Existing preferences | Header, logo, breadcrumb, tags and TopNav toggles round trip | Hidden header frees content height; recovery works; hidden-sidebar profile uses full-width header |
| TopNav overflow | 1024px overflow contains and selects engineering group | Last route no longer clipped by header actions |
| Shared login brand | Heading retained; 390px title wraps | Login card fits between x=24 and x=366 in 390px viewport |
| Theme boundaries | Compare all 11 targeted baselines | Zero added core variable assignments; original toolbar hierarchy retained |

Exploratory checks covered nested log selection from the rail, expanding back to the active leaf, header-hidden mobile recovery, profile navigation hiding the sidebar, and shared login rendering. Independent review found one P2 in the initial manual mobile focus path; that finding was fixed through native Drawer. The follow-up review found no remaining P1/P2 in the reviewed changes.

Viewport checks: at 768px and 390px, the header spans the viewport at 56px height; the rightmost user control ends at 752px and 382px respectively. Document scroll widths equal viewport widths. Header/sidebar screenshots were inspected for unintended clipping, overlap, duplicated branding and unreachable controls. Sidebar scrolling remains available for long menus. Business table/filter reflow is outside this navigation task.

## Verification

- `yarn vitest run tests/unit/Hamburger.test.ts src/layout/policy.test.ts`: **9 passed**. The accessible toggle regression failed before implementation because the old control was a clickable div.
- Targeted ESLint across the eight affected Vue files and the existing Hamburger test: **passed**.
- `yarn type-check`: **passed**.
- Targeted `git diff --check`: **passed**.
- Local runtime browser errors during the final verification: **0**.
- Resource inspection confirmed `/@fs/Users/hqz/Downloads/element-plus/packages/zxui/` modules in the running application.
- `validate.sh --changed`: still fails on three pre-existing workspace findings: deleted simulation `AlarmPanelFloating.vue`, a hardcoded colour in `FaultBoardPanel.vue`, and an axios policy match in `session.test.ts`. No claim of a clean full-workspace gate is made.
- Production build and backend suites were not run for this source-linked navigation change.

## Evidence

- [Default light, expanded](navigation-shell-2026-10-22/expanded-default.png)
- [Army-pine dark, expanded](navigation-shell-2026-10-22/expanded-army-dark.png)
- [Rail with nested popup](navigation-shell-2026-10-22/collapsed-popup-army-dark.png)
- [1024px TopNav overflow](navigation-shell-2026-10-22/topnav-1024.png)
- [Mobile default drawer](navigation-shell-2026-10-22/mobile-drawer-default.png)
- [Mobile army-pine drawer](navigation-shell-2026-10-22/mobile-drawer-army-dark.png)
- [Mobile closed navigation](navigation-shell-2026-10-22/mobile-closed-default.png)
- [390px login brand](navigation-shell-2026-10-22/login-390.png)
- [Checks and measured geometry](navigation-shell-2026-10-22/checks.json)

## User feedback follow-up

The first implementation missed desktop width animation and normal-item popup colour after teleport. Both were reproduced and corrected in the business integration; see [the follow-up report](2026-10-22-navigation-shell-feedback.md) for causes, corrected screenshots and frame measurements. Earlier popup screenshots are historical and are superseded by that report.
