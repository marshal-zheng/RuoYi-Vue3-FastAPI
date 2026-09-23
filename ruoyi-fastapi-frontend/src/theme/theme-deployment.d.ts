/** App-owned Vite data module; library contracts remain in the ZXUI package. */
declare module 'virtual:zxui-theme-deployment' {
  const data: import('./zx-theme-host').ZxThemeDeploymentData;
  export default data;
}
