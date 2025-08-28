/// <reference types="vitest" />
/// <reference types="@testing-library/jest-dom" />

declare module '*.vue' {
  const component: any
  export default component
}