import { editorThemeOwnerKey, type EditorThemeOwner } from '@zxio/text-editor';
import { createShortcutRuntime } from '@zxio/keybindings/core';
import { createShortcutPlugin } from '@zxio/keybindings/vue';

/** Public ports in a DOM test; this does not verify theme assets or browser layout. */
export function createRemarkFieldTestHost(appId: string) {
  const portal = document.createElement('div');
  const success = async () => ({ ok: true, value: undefined, diagnostics: [] });
  const owner = {
    runtimeId: appId,
    scopeId: appId,
    state: 'active',
    feedback: { message: success, notification: success, confirm: success },
    acquirePortal: async () => ({
      ok: true,
      diagnostics: [],
      value: {
        runtimeId: appId,
        scopeId: appId,
        target: portal,
        appContext: {},
        themeId: 'test',
        variantKey: 'test',
        release() {},
      },
    }),
    dispose: () => ({ ok: true, value: undefined, diagnostics: [] }),
  } as unknown as EditorThemeOwner;
  return {
    portal,
    get global() {
      return {
        provide: { [editorThemeOwnerKey as symbol]: owner },
        // Each mounted Vue app owns its runtime. DOM runners require an explicit platform.
        plugins: [createShortcutPlugin(createShortcutRuntime({ appId, platform: 'mac' }))],
      };
    },
    attach: () => document.body.append(portal),
    dispose: () => {
      portal.replaceChildren();
      portal.remove();
    },
  };
}
