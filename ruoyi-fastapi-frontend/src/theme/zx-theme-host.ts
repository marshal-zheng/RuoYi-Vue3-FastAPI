import type { ThemeDeploymentOutput } from '@zxio/theme-compiler/deployment';
import { createBoundConfirmInputFactory } from '@zxio/zxui/confirm-input';
import {
  bindThemePreferenceController,
  createDefaultBrowserThemeHost,
  createThemeDeploymentResolver,
} from '@zxio/zxui/theme-host/precompiled';
import type { App } from 'vue';
import { ElMessage } from 'element-plus';

import { setBoundConfirmInputFactoryProvider } from './confirm-input';
import { zxThemePreferences, zxThemePreference } from './zx-theme-config';
import {
  ZX_DEFAULT_THEME_ID,
  ZX_THEME_MANIFEST_LIMIT,
  ZX_THEME_PACKAGE_CHOICES,
} from './zx-theme-packages';

function diagnosticMessage(
  diagnostics: readonly {
    code: string;
    details?: Readonly<Record<string, unknown>>;
  }[]
): string {
  return diagnostics.map((item) => `${item.code}:${JSON.stringify(item.details ?? {})}`).join(', ');
}

export function bindZxThemeHost(app: App, themeDeployment: ThemeDeploymentOutput): void {
  for (const choice of ZX_THEME_PACKAGE_CHOICES) {
    if (
      !themeDeployment.registrations.some(
        ({ manifest }) =>
          manifest.identity.themeId === choice.id &&
          manifest.identity.packageName === choice.packageName
      )
    ) {
      throw new Error(`Missing registered ZXUI theme manifest: ${choice.packageName}/${choice.id}`);
    }
  }
  const assetResolver = createThemeDeploymentResolver({
    deployment: themeDeployment.deployment,
    baseURL: new URL(import.meta.env.BASE_URL, document.baseURI).href,
  });
  if (!assetResolver.ok) {
    throw new Error(
      `Failed to resolve ZXUI theme deployment: ${diagnosticMessage(assetResolver.diagnostics)}`
    );
  }
  const host = createDefaultBrowserThemeHost({
    appKey: 'vfadmin',
    defaultThemeId: ZX_DEFAULT_THEME_ID,
    maxRegisteredManifests: ZX_THEME_MANIFEST_LIMIT,
    themes: themeDeployment.registrations,
    assetResolver: assetResolver.value,
    stylesheetPolicy: 'on-demand',
    portalTarget: () => document.body,
    // EP's document poppers require the committed root identity on their container.
    // Nested ZXUI scopes keep their own Provider/Portal binding.
    portalContainerScope: 'mirrored',
    rootRequest: zxThemePreference.value,
  });
  if (!host.ok) {
    throw new Error(`Failed to create ZXUI theme host: ${diagnosticMessage(host.diagnostics)}`);
  }
  const bound = host.value.bind(app);
  if (!bound.ok) {
    throw new Error(`Failed to bind ZXUI theme host: ${diagnosticMessage(bound.diagnostics)}`);
  }
  const stopPreferences = bindThemePreferenceController(
    zxThemePreferences,
    host.value.runtime,
    bound.value,
    (issue) => {
      if (issue === 'storage-unavailable') {
        ElMessage.warning('界面设置已生效，但无法保存到本地。');
      } else {
        ElMessage.error('界面设置切换失败，已恢复上次设置，请重试。');
      }
    }
  );
  setBoundConfirmInputFactoryProvider(() => {
    const factory = createBoundConfirmInputFactory(host.value.runtime, bound.value);
    if (!factory.ok) {
      throw new Error(
        `Failed to create ZXUI confirm-input factory: ${diagnosticMessage(factory.diagnostics)}`
      );
    }
    return factory.value;
  });
  app.onUnmount(() => {
    stopPreferences();
    void host.value.dispose();
  });
}
