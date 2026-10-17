/** Test-only module target for the Vite deployment plugin's virtual entry. */
export default {
  schema: 'zx.theme-runtime-deployment/1',
  deployment: { schema: 'zx.theme-deployment/1', manifests: [], entries: [] },
  registrations: [],
} satisfies import('@zxio/theme-compiler/deployment').ThemeRuntimeDeploymentOutput;
