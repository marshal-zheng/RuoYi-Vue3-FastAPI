import { compileTemplate } from '@vue/compiler-sfc';
import { describe, expect, it } from 'vitest';

interface ComponentImportPlugin {
  configResolved(config: { root: string; plugins: never[]; build: object; command: string }): void;
  transformInclude(file: string): boolean;
  transform: {
    call(
      context: { error(error: unknown): never },
      code: string,
      file: string
    ): Promise<{ code: string }>;
  };
}

async function transform(template: string) {
  const { default: createComponentImports } = await import('../vite/plugins/components');
  const plugin = createComponentImports() as unknown as ComponentImportPlugin;
  plugin.configResolved({
    root: process.cwd(),
    plugins: [],
    build: {},
    command: 'build',
  });
  const file = `${process.cwd()}/src/views/on-demand-fixture.vue`;
  const code = compileTemplate({
    source: template,
    filename: file,
    id: 'fixture',
  }).code;
  const result = await plugin.transform.call(
    {
      error: (error: unknown) => {
        throw error;
      },
    },
    code,
    file
  );
  return result.code as string;
}

describe('application component imports', () => {
  it('limits host auto imports to application Vue templates', async () => {
    const { default: createComponentImports } = await import('../vite/plugins/components');
    const plugin = createComponentImports() as unknown as ComponentImportPlugin;
    expect(plugin.transformInclude(`${process.cwd()}/src/views/fixture.vue`)).toBe(true);
    expect(
      plugin.transformInclude(`${process.cwd()}/src/views/fixture.vue?vue&type=template`)
    ).toBe(true);
    expect(plugin.transformInclude('/Users/library/packages/components/input/src/input.vue')).toBe(
      false
    );
    expect(plugin.transformInclude(`${process.cwd()}/node_modules/other/src/input.vue`)).toBe(
      false
    );
  });

  it('imports public ZXUI core components, EP components/directives and actual icon objects', async () => {
    const code = await transform(
      '<ZxInput /><ZxDialog /><el-select /><Plus /><div v-loading="busy" />'
    );
    expect(code).toContain('@zxio/zxui/core');
    expect(code).not.toContain('@zxio/zxui/input');
    expect(code).not.toContain('@zxio/zxui/dialog');
    expect(code).toContain('element-plus/es');
    expect(code).toContain('ElLoadingDirective');
    expect(code).toContain('@element-plus/icons-vue');
    expect(code).not.toContain('@zxio/components');
    expect(code).not.toContain('/style');
  });

  it('leaves application-owned and feature-owned component names alone', async () => {
    const code = await transform('<DictSelect /><ZxChart /><DevicePicker />');
    expect(code).toContain('_resolveComponent("DictSelect")');
    expect(code).toContain('_resolveComponent("ZxChart")');
    expect(code).toContain('_resolveComponent("DevicePicker")');
    expect(code).not.toContain('@zxio/zxui');
  });
});
