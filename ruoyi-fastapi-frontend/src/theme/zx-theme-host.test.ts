import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createApp, nextTick, shallowRef } from 'vue';
import { ZX_THEME_PACKAGE_CHOICES } from './zx-theme-packages';

const api = vi.hoisted(() => ({
  createHost: vi.fn(),
  createResolver: vi.fn(),
  createConfirm: vi.fn(),
}));
vi.mock('@zxio/zxui/theme-host', () => ({
  createDefaultBrowserThemeHost: api.createHost,
  createThemeDeploymentResolver: api.createResolver,
}));
vi.mock('@zxio/zxui', () => ({
  createBoundConfirmInputFactory: api.createConfirm,
}));

import { bindZxThemeHost } from './zx-theme-host';

const deployment = {
  deployment: { schema: 'zx.theme-deployment/1' },
  registrations: ZX_THEME_PACKAGE_CHOICES.map(({ id, packageName }) => ({
    manifest: { identity: { themeId: id, packageName } },
  })),
};

beforeEach(() => {
  vi.stubEnv('BASE_URL', '/admin/');
  api.createResolver.mockReturnValue({ ok: true, value: { resolve: vi.fn() } });
});

describe('public theme deployment host', () => {
  it('uses the application base and projects only a committed Host scope', async () => {
    const rootScope = shallowRef<unknown>(null);
    api.createHost.mockReturnValue({
      ok: true,
      value: {
        runtime: {},
        bind: () => ({ ok: true, value: { rootScope } }),
        dispose: vi.fn(),
      },
    });
    const app = createApp({ template: '<div />' });
    bindZxThemeHost(app, deployment);
    expect(api.createResolver).toHaveBeenCalledWith({
      deployment: deployment.deployment,
      baseURL: new URL('/admin/', document.baseURI).href,
    });
    expect(api.createHost.mock.calls[0][0].themes).toBe(deployment.registrations);
    rootScope.value = {
      state: 'ready',
      resolved: {
        themeId: 'tech-blue',
        variantKey: 'host-variant',
        selection: { mode: 'dark' },
      },
    };
    await nextTick();
    expect(document.documentElement.dataset.zxTheme).toBe('tech-blue');
    expect(document.documentElement.dataset.zxVariant).toBe('host-variant');
  });

  it('rejects incomplete registrations instead of silently falling back', () => {
    expect(() =>
      bindZxThemeHost(createApp({}), {
        ...deployment,
        registrations: deployment.registrations.slice(1),
      })
    ).toThrow('Missing registered ZXUI theme manifest');
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
