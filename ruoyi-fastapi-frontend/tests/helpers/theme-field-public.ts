import { createApp, ref } from 'vue';
import manifest from '@zxio/theme-default/manifest.json';
import { themeRuntimeKey, themeScopeKey, themePortalTargetKey } from '@zxio/zxui/theme-provider';
import {
  createBrowserThemeRuntime,
  createThemeAssetCache,
  createThemeAssetResolver,
  createThemeTargetCoordinator,
  createThemeTargetCoordinatorResolver,
  providerOwnedAdapterContract,
} from '@zxio/zxui/theme-runtime';

/** Real public theme runtime and portal lifetime. CSS payloads are test ports, not visual evidence. */
export async function createFieldThemeTestHost() {
  const hashes = new Map<string, string>();
  hashes.set('./theme.css', manifest.artifacts.find(({ path }) => path === 'theme.css')!.sha256);
  hashes.set(
    './element-plus.css',
    manifest.artifacts.find(({ path }) => path === 'element-plus/aliases.css')!.sha256
  );
  for (const variant of manifest.variants) {
    hashes.set(`./variants/${variant.variantKey}`, variant.artifacts.coreCss.sha256);
    hashes.set(
      `./element-plus/${variant.variantKey}`,
      variant.artifacts.elementPlusResolvedCss.sha256
    );
  }
  const cache = createThemeAssetCache();
  const runtime = createBrowserThemeRuntime({
    runtimeId: 'user-schema-test',
    themes: [{ manifest }],
    defaultThemeId: 'default',
    adapterContract: providerOwnedAdapterContract,
    assetCache: cache,
    assetResolver: createThemeAssetResolver({
      exports: {
        async resolve({ exportPath }) {
          return { ok: true, value: { kind: 'css-text', text: exportPath }, diagnostics: [] };
        },
      },
      digestText: async (text) => hashes.get(text)!,
    }),
    targetCoordinatorResolver: createThemeTargetCoordinatorResolver([
      createThemeTargetCoordinator(document),
    ]),
    stylesheetPolicy: 'on-demand',
    systemPreference: { currentMode: () => 'light', subscribe: () => () => {} },
  });
  if (!runtime.ok) throw new Error('Test theme runtime failed');
  const bound = runtime.value.bindVueApp(createApp({}), { appKey: 'user-schema', rootRequest: {} });
  if (!bound.ok) throw new Error('Test theme binding failed');
  const root = document.body.appendChild(document.createElement('main'));
  const target = document.body.appendChild(document.createElement('section'));
  const scope = await runtime.value.activateScope(bound.value.preparedRoot, { root });
  if (!scope.ok) throw new Error('Test theme scope failed');
  return {
    root,
    provide: {
      [themeRuntimeKey as symbol]: runtime.value,
      [themeScopeKey as symbol]: ref(scope.value),
      [themePortalTargetKey as symbol]: ref(target),
    },
    async dispose() {
      scope.value.dispose();
      await runtime.value.dispose();
      await cache.dispose();
      root.remove();
      target.remove();
    },
  };
}
