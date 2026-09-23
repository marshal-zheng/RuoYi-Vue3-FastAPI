import { createBoundConfirmInputFactory } from '@zxio/zxui';
import {
  createDefaultBrowserThemeHost,
  createThemeDeploymentResolver,
} from '@zxio/zxui/theme-host';
import { watch, type App } from 'vue';

import { setBoundConfirmInputFactoryProvider } from './confirm-input';
import { projectZxThemeScope, zxThemePreference } from './zx-theme-config';
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

export interface ZxThemeDeploymentData {
  readonly deployment: unknown;
  readonly registrations: readonly {
    readonly manifest: {
      readonly identity: {
        readonly themeId: string;
        readonly packageName: string;
      };
    };
  }[];
}

export function bindZxThemeHost(app: App, themeDeployment: ZxThemeDeploymentData): void {
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
  const stopProjection = watch(
    bound.value.rootScope,
    (scope) => {
      if (scope?.state === 'ready') projectZxThemeScope(scope.resolved);
    },
    { immediate: true }
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
    stopProjection();
    void host.value.dispose();
  });
}
