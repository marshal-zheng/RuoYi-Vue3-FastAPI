import { createApp, defineComponent, h, resolveComponent } from 'vue';
import { afterEach, describe, expect, it, vi } from 'vitest';
import VXETable from 'vxe-table';
import * as tableSetup from './vxe-table';
import { installVxeThemeLayout } from './vxe-layout';

vi.mock('./vxe-layout', () => ({ installVxeThemeLayout: vi.fn() }));

afterEach(() => vi.restoreAllMocks());

describe('VXE registration at the table consumer', () => {
  it('installs once per application while retaining a separate application owner', () => {
    const first = createApp({});
    const second = createApp({});
    const renderer = vi.spyOn(VXETable.renderer, 'add');
    const warning = vi.spyOn(console, 'warn');

    tableSetup.setupVXETable(first);
    tableSetup.setupVXETable(first);
    tableSetup.setupVXETable(second);

    const dictionaryCalls = renderer.mock.calls.filter(([name]) => name === 'DictAutocomplete');
    expect(dictionaryCalls).toHaveLength(1);
    expect(installVxeThemeLayout).toHaveBeenCalledTimes(2);
    expect(first.component('VxeTable')).toBe(second.component('VxeTable'));
    expect(first.component('VxeColumn')).toBeDefined();
    expect(warning).not.toHaveBeenCalled();
  });

  it('uses the installed nested Chinese locale and formats diagnostic arguments', () => {
    tableSetup.setupVXETable(createApp({}));
    expect(VXETable.getI18n('vxe.table.emptyText')).toBe('暂无数据');
    expect(
      VXETable.getI18n('vxe.error.coverProp', ['Renderer.DictAutocomplete', 'renderEdit'])
    ).toBe('"Renderer.DictAutocomplete" 的参数 "renderEdit" 重复定义，这可能会出现错误');
  });

  it('registers the table before the first consumer render resolves its name', () => {
    expect(tableSetup).toHaveProperty('useVXETable', expect.any(Function));
    const useVXETable = Reflect.get(tableSetup, 'useVXETable') as () => void;
    let resolved: unknown;
    const app = createApp(
      defineComponent({
        setup() {
          useVXETable();
          return () => {
            resolved = resolveComponent('vxe-table');
            return h('div');
          };
        },
      })
    );
    app.mount(document.createElement('div'));
    try {
      expect(resolved).toBe(app.component('VxeTable'));
      expect(resolved).not.toBeTypeOf('string');
    } finally {
      app.unmount();
    }
  });
});
