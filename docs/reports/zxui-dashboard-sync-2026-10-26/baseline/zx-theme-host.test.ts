import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createApp, nextTick, shallowRef } from 'vue';
import { ZX_THEME_PACKAGE_CHOICES } from './zx-theme-packages';
import type { ThemeRuntimeDeploymentOutput } from '@zxio/theme-compiler/deployment';

const api = vi.hoisted(() => ({
  createHost: vi.fn(),
  createFullHost: vi.fn(),
  createResolver: vi.fn(),
  createConfirm: vi.fn(),
  bindPreferences: vi.fn(),
}));
vi.mock('@zxio/zxui/theme-host', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@zxio/zxui/theme-host')>()),
  createDefaultBrowserThemeHost: api.createFullHost,
  createThemeDeploymentResolver: api.createResolver,
  bindThemePreferenceController: api.bindPreferences,
}));
vi.mock('@zxio/zxui/theme-host/precompiled', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@zxio/zxui/theme-host/precompiled')>()),
  createDefaultBrowserThemeHost: api.createHost,
  createThemeDeploymentResolver: api.createResolver,
  bindThemePreferenceController: api.bindPreferences,
}));
vi.mock('@zxio/zxui/core', () => ({
  createBoundConfirmInputFactory: api.createConfirm,
}));

import { bindZxThemeHost } from './zx-theme-host';
import { zxThemePreferences } from './zx-theme-config';

// The resolver and Host are mocked here; this fixture only exercises app wiring.
const deployment = {
  schema: 'zx.theme-runtime-deployment/1',
  deployment: { schema: 'zx.theme-deployment/1' },
  registrations: ZX_THEME_PACKAGE_CHOICES.map(({ id, packageName }) => ({
    runtime: { identity: { themeId: id, packageName } },
  })),
} as unknown as ThemeRuntimeDeploymentOutput;

beforeEach(() => {
  vi.clearAllMocks();
  api.createFullHost.mockImplementation(() => {
    throw new Error('The application consumes precompiled theme variants');
  });
  vi.stubEnv('BASE_URL', '/admin/');
  api.createResolver.mockReturnValue({ ok: true, value: { resolve: vi.fn() } });
});

describe('public theme deployment host', () => {
  it('binds the Host-owned preference lifecycle without projecting DOM from business code', async () => {
    const release = vi.fn();
    const dispose = vi.fn();
    api.bindPreferences.mockReturnValue(release);
    document.documentElement.removeAttribute('data-zx-theme');
    document.documentElement.removeAttribute('data-zx-variant');
    const rootScope = shallowRef<unknown>(null);
    api.createHost.mockReturnValue({
      ok: true,
      value: {
        runtime: {},
        bind: () => ({ ok: true, value: { rootScope } }),
        dispose,
      },
    });
    const app = createApp({ template: '<div />' });
    bindZxThemeHost(app, deployment);
    expect(api.createFullHost).not.toHaveBeenCalled();
    expect(api.createHost).toHaveBeenCalledOnce();
    expect(api.createResolver).toHaveBeenCalledWith({
      deployment: deployment.deployment,
      baseURL: new URL('/admin/', document.baseURI).href,
    });
    expect(api.createHost.mock.calls[0][0].themes).toBe(deployment.registrations);
    expect(api.createHost.mock.calls[0][0]).not.toHaveProperty('seedPolicy');
    expect(api.createHost.mock.calls[0][0]).not.toHaveProperty('composition.seeds');
    rootScope.value = {
      state: 'ready',
      resolved: {
        themeId: 'tech-blue',
        variantKey: 'host-variant',
        selection: { mode: 'dark' },
      },
    };
    await nextTick();
    expect(api.bindPreferences).toHaveBeenCalledWith(
      zxThemePreferences,
      api.createHost.mock.results[0].value.value.runtime,
      expect.objectContaining({ rootScope }),
      expect.any(Function)
    );
    expect(document.documentElement.dataset.zxTheme).toBeUndefined();
    expect(document.documentElement.dataset.zxVariant).toBeUndefined();
    app.mount(document.createElement('div'));
    app.unmount();
    expect(release).toHaveBeenCalledOnce();
    expect(dispose).toHaveBeenCalledOnce();
  });

  it('rejects incomplete registrations instead of silently falling back', () => {
    expect(() =>
      bindZxThemeHost(createApp({}), {
        ...deployment,
        registrations: deployment.registrations.slice(1),
      })
    ).toThrow('Missing registered ZXUI runtime theme');
  });

  it('surfaces deployment diagnostics', () => {
    api.createResolver.mockReturnValue({
      ok: false,
      diagnostics: [
        {
          code: 'TR_ASSET_REF_INVALID',
          details: { reason: 'deployment-schema-invalid' },
        },
      ],
    });
    expect(() => bindZxThemeHost(createApp({}), deployment)).toThrow('deployment-schema-invalid');
  });
});
