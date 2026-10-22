import path from 'node:path';
import Components from 'unplugin-vue-components/vite';
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers';
import * as elementIcons from '@element-plus/icons-vue';
import { ZxuiResolver } from '@zxio/zxui/resolver';
import type { PluginOption } from 'vite';

/** Components belong to their consuming route; styles are ordered by main.ts. */
export default function createComponentImports(): PluginOption {
  const sourceRoot = path.resolve(process.cwd(), 'src').replace(/\\/g, '/');
  const escapedRoot = sourceRoot.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return Components({
    include: [new RegExp(`^${escapedRoot}/.*\\.vue(?:\\?.*)?$`)],
    dirs: [],
    dts: false,
    resolvers: [
      ZxuiResolver({ importStyle: false, entry: 'core' }),
      ElementPlusResolver({ importStyle: false, directives: true }),
      (name) =>
        Object.prototype.hasOwnProperty.call(elementIcons, name)
          ? { name, from: '@element-plus/icons-vue' }
          : undefined,
    ],
  });
}
