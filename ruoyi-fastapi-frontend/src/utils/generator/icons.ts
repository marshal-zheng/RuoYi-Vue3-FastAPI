import { defineAsyncComponent } from 'vue';
import type { Component } from 'vue';
import { elementIcons } from '@/icons/element';
import { isElementIconName } from './icon-name';

const dynamicIcons = new Map<string, Component>();

/** Saved designs retain string names; only the preview resolves concrete components. */
export function resolveGeneratorIcon(name: string): Component {
  if (Object.hasOwn(elementIcons, name)) return elementIcons[name];
  if (!isElementIconName(name)) return () => null;
  let icon = dynamicIcons.get(name);
  if (!icon) {
    icon = defineAsyncComponent(async () => {
      const { icons: catalog } = await import('@/views/tool/build/element-catalog');
      return Object.hasOwn(catalog, name)
        ? (catalog as Record<string, Component>)[name]
        : () => null;
    });
    dynamicIcons.set(name, icon);
  }
  return icon;
}
