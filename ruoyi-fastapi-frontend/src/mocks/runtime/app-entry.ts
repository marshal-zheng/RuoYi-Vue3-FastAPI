import type { RuntimeConfig } from './mode';

type SetupMockRuntime = (typeof import('./setup'))['setupMockRuntime'];

async function loadDefaultMockRuntime(): Promise<SetupMockRuntime> {
  const runtime = await import('./setup');
  return runtime.setupMockRuntime;
}

export function clearRuntimeDevtools() {
  if (typeof window === 'undefined') {
    return;
  }

  delete (window as Window & { __DEMO_RUNTIME__?: unknown }).__DEMO_RUNTIME__;
  delete window.__MOCK_RUNTIME__;
}

export async function setupAppRuntimeMocks(
  runtimeConfig: RuntimeConfig,
  setupRuntime?: SetupMockRuntime
): Promise<void> {
  clearRuntimeDevtools();

  if (runtimeConfig.mode === 'real') {
    return;
  }

  const runSetup = setupRuntime ?? (await loadDefaultMockRuntime());

  await runSetup({
    mode: runtimeConfig.mode,
    apiPrefix: runtimeConfig.apiPrefix,
    debug: runtimeConfig.debug,
  });
}
