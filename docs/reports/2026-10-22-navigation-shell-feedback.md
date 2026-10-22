# Navigation Feedback Correction — 2026-10-22

Implemented the two user-reported gaps in the existing business shell. ZXUI palette, theme assets and component sources were not changed.

## Root causes

1. Desktop grid columns had no transition; the sidebar and content moved directly between 250px and 64px. A pre-fix RAF probe saw only the final width and a computed duration of 0s.
2. Business ElMenu colour props referenced aliases declared on the sidebar. Element Plus forwards those props as inline menu variables into teleported popup menus, where the sidebar aliases are absent. The normal item text became `rgb(0, 0, 0)` although the existing army-pine overlay text token was correct. Its colour helper also interpreted a CSS variable expression as black for hover. The prior review missed normal-item colour while checking selected items.

## Corrections

- Animate the existing grid columns with the ThingsBoard timing curve, consuming twice the current ZXUI semantic motion duration. Sidebar width follows the grid track, keeping sidebar/header/main aligned. In army-pine this is 280ms.
- Fade the retained brand and rotate the toggle; collapsed brand content is both aria-hidden and inert. Mobile, hidden-sidebar, withoutAnimation and system reduced-motion paths skip the desktop grid transition.
- Keep the rail menu anchored at the final rail width during animation, so icons do not move to the centre of the expanded sidebar.
- Remove the three local colour props. Popup background/text now consume existing overlay token pairs; selected state retains selected tokens, and hover/focus consume existing theme roles. No hardcoded white/black or core theme variable overrides were added.

Changed sources: layout/index.vue, layout/components/Sidebar/index.vue, assets/styles/sidebar.css and components/ui/Hamburger/index.vue under ruoyi-fastapi-frontend/src.

## Verification

- Real source-linked local business: expansion and collapse contain continuous intermediate widths. Header/main X match sidebar width in every sampled frame. Rail icon centre remains 31.5px throughout collapse.
- Fast reverse toggle ends with the expanded active path visible. System reduced-motion samples remain 64px with computed transition duration 0s.
- Default and army-pine, light and dark: settled normal popup text/background contrast ratios measured 15.17, 14.32, 15.38 and 10.75 respectively. These are measurements of the existing theme colours, not new palettes. Normal/selected/hover and nested log menus were checked.
- Mobile drawer still opens at its control and Escape returns focus to the launcher. Final browser errors: 0.
- Existing focused tests: 9 passed; targeted ESLint and diff whitespace check passed. Type check passed.
- Independent review found an intermediate rail-icon drift; it was corrected and frame-verified. Final review has no remaining P1/P2 in these four files.
- The repository-wide changed-file convention script retains the same three existing findings: missing AlarmPanelFloating.vue, colour policy in FaultBoardPanel.vue, and axios policy in session.test.ts. No claim of a clean whole-workspace gate.

## Evidence

- [Corrected army-pine popup](navigation-shell-feedback-2026-10-22/popup-army-dark.png)
- [Default light popup](navigation-shell-feedback-2026-10-22/popup-default-light.png)
- [Default dark popup](navigation-shell-feedback-2026-10-22/popup-default-dark.png)
- [Nested army-pine popup](navigation-shell-feedback-2026-10-22/nested-popup-army-dark.png)
- [Mobile drawer](navigation-shell-feedback-2026-10-22/mobile-army-dark.png)
- [Frame samples, colours and checks](navigation-shell-feedback-2026-10-22/checks.json)
