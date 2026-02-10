# Tailwind and Theme Reference

Styling guidance for the current frontend stack (Tailwind v4 + CSS variables + LESS).

## 1. Token source files

Primary token definitions live in:

- `src/assets/styles/tailwind.css`
- `src/assets/styles/theme.module.css`
- `src/assets/styles/design-tokens.css`

When introducing reusable colors, define them in token files first.

## 2. Styling priority

1. Tailwind utility classes for layout/spacing/typography.
2. CSS variables for color and semantic theme values.
3. Scoped component styles for local structure.
4. `:deep()` for controlled overrides of library internals.
5. LESS only when extending existing global style architecture.

## 3. Color policy

Project is in brownfield state. Legacy hardcoded colors exist.

Policy for new edits:

1. Do not introduce new hex colors in non-token files.
2. Prefer `var(--el-*)` or Tailwind theme classes.
3. For visualization-heavy modules that require fixed palette values, document intent in code comments and keep additions minimal.

## 4. Dark mode

- Dark mode is driven by `.dark` and CSS variable overrides.
- Prefer token-based styling so light/dark adapts automatically.
- Avoid duplicate full dark-only style files for new modules unless explicitly requested.

## 5. Element Plus bridge

Element Plus tokens are mapped through CSS variables. Prefer:

```css
color: var(--el-text-color-primary);
border-color: var(--el-border-color);
background: var(--el-bg-color);
```

Do not edit Element Plus internals directly.
