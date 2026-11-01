import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { ref, type Component } from 'vue';
import ElementPlus from 'element-plus';
import { createShortcutRuntime } from '@zxio/keybindings';
import { createShortcutPlugin } from '@zxio/keybindings/vue';
import type { TableRenderInstance } from '@zxio/table-render/ui';
import ConfigList from '@/views/system/config/components/ConfigList.vue';
import MenuList from '@/views/system/menu/components/MenuList.vue';
import { endQuerySession, setQuerySession } from '@/queries/context';
const api = vi.hoisted(() => ({
  listConfig: vi.fn(),
  delConfig: vi.fn(),
  refreshCache: vi.fn(),
  listMenu: vi.fn(),
  delMenu: vi.fn(),
  confirm: vi.fn(),
  message: vi.fn(),
  download: vi.fn(),
  permission: vi.fn(),
  open: vi.fn(),
}));
vi.mock('@/api/system/config', () => api);
vi.mock('@/api/system/menu', () => api);
vi.mock('@/utils/permission', () => ({ checkPermi: api.permission }));
vi.mock('@zxio/zxui/theme-provider', async (original) => ({
  ...(await original<object>()),
  useThemeFeedback: () => ({ ok: true, value: api }),
}));
vi.mock('@/views/system/config/components/ConfigDlg.vue', () => ({
  default: {
    setup(_: unknown, { expose }: { expose: (value: unknown) => void }) {
      expose({ open: api.open });
      return () => null;
    },
  },
}));
vi.mock('@/views/system/menu/components/MenuDrawer.vue', () => ({
  default: {
    setup(_: unknown, { expose }: { expose: (value: unknown) => void }) {
      expose({ open: api.open });
      return () => null;
    },
  },
}));
vi.mock('@/components/ui/Remark/RemarkDisplay.vue', () => ({
  default: { props: ['text'], template: '<span>{{ text }}</span>' },
}));
const mounted: ReturnType<typeof mount>[] = [];
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}
function page(component: Component) {
  const wrapper = mount(component, {
    global: {
      plugins: [
        ElementPlus,
        createShortcutPlugin(createShortcutRuntime({ appId: 'request-pages', platform: 'mac' })),
      ],
      config: {
        globalProperties: {
          download: api.download,
          useDict: () => ({ sys_yes_no: ref([]), sys_normal_disable: ref([]) }),
        } as never,
      },
      stubs: {
        DictStatus: true,
        DictSelect: true,
        DictTag: true,
        ZxIcon: true,
        ZxButton: {
          emits: ['click'],
          template: '<button @click="$emit(\'click\')"><slot /></button>',
        },
      },
    },
  });
  mounted.push(wrapper);
  const table = () =>
    wrapper.getComponent({ name: 'ZxTableRender' }).vm as unknown as TableRenderInstance<
      never,
      { configId: number },
      {
        configName?: string;
        configKey?: string;
        configType?: string;
        dateRange?: string[];
        menuName?: string;
      }
    >;
  const button = (label: string) =>
    wrapper.findAll('button').find((node) => node.text().trim() === label)!;
  return { wrapper, table, button };
}
beforeEach(() => {
  vi.resetAllMocks();
  setQuerySession(1, ['admin'], ['*:*:*']);
  api.permission.mockReturnValue(true);
  api.listConfig.mockImplementation(async (query) => ({
    items: [{ configId: query.page === 2 ? 12 : 2, configName: '配置', remarkText: '富文本摘要' }],
    total: 21,
    page: query.page,
    pageSize: query.pageSize,
  }));
  api.listMenu.mockResolvedValue({
    items: Object.freeze([
      Object.freeze({ menuId: 1, parentId: 0, menuName: '系统' }),
      Object.freeze({ menuId: 2, parentId: 1, menuName: '配置' }),
    ]),
  });
  api.confirm.mockResolvedValue({ ok: true, value: 'confirm' });
  api.open.mockResolvedValue(undefined);
});
afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
});

describe('request-mode real business consumers', () => {
  it('serializes dates once and exports successful applied query rather than draft or pager', async () => {
    const { table, button, wrapper } = page(ConfigList);
    await flushPromises();
    table().setDraft({
      configName: 'filtered',
      configKey: 'test.key',
      configType: 'N',
      dateRange: ['2026-10-01', '2026-10-16'],
    });
    await table().search();
    await flushPromises();
    await table().requery({ page: 2 });
    await flushPromises();
    const filters = {
      configName: 'filtered',
      configKey: 'test.key',
      configType: 'N',
      beginTime: '2026-10-01',
      endTime: '2026-10-16',
    };
    expect(api.listConfig.mock.calls.at(-1)?.[0]).toEqual({ ...filters, page: 2, pageSize: 10 });
    table().setDraft({ configName: 'unsent' });
    await button('导出').trigger('click');
    expect(api.download).toHaveBeenCalledWith('system/config/export', filters, expect.any(String));
    expect(wrapper.text()).toContain('富文本摘要');
    expect(api.listConfig.mock.calls[0][1].signal).toBeInstanceOf(AbortSignal);
  });
  it('keeps same-query rows after failure, retries, and clears page selection on a successful page change', async () => {
    const { table, wrapper } = page(ConfigList);
    await flushPromises();
    await wrapper.get('thead input[type=checkbox]').setValue(true);
    expect(table().selection.keys).toEqual([2]);
    api.listConfig.mockRejectedValueOnce(new Error('read failed'));
    await table().reload();
    await flushPromises();
    expect(wrapper.get('tbody').text()).toContain('配置');
    expect(wrapper.text()).toMatch(/Refresh failed|失败/);
    await table().reload();
    await table().requery({ page: 2 });
    await flushPromises();
    expect(table().selection.keys).toEqual([]);
  });
  it('confirms the selected target, blocks duplicate writes and retires confirmation across domains', async () => {
    const { table, wrapper, button } = page(ConfigList);
    await flushPromises();
    await wrapper.get('thead input[type=checkbox]').setValue(true);
    const confirmation = deferred<{ ok: true; value: 'confirm' }>();
    api.confirm.mockReturnValue(confirmation.promise);
    await button('删除').trigger('click');
    expect(api.confirm.mock.calls[0][0].message).toContain('2');
    setQuerySession(2, ['admin'], ['*:*:*']);
    confirmation.resolve({ ok: true, value: 'confirm' });
    await flushPromises();
    expect(api.delConfig).not.toHaveBeenCalled();
    expect(table().selection.keys).toEqual([]);
    api.confirm.mockResolvedValue({ ok: true, value: 'confirm' });
    const saving = deferred<void>();
    api.delConfig.mockReturnValue(saving.promise);
    const rowDelete = wrapper.get('tbody [data-zx-action-id="delete"]');
    await rowDelete.trigger('click');
    await rowDelete.trigger('click');
    await flushPromises();
    expect(api.delConfig).toHaveBeenCalledTimes(1);
    saving.resolve();
    await flushPromises();
  });
  it('expands the menu tree without remounting, mutating transport data or issuing another read', async () => {
    const { table, wrapper, button } = page(MenuList);
    await flushPromises();
    const instance = wrapper.getComponent({ name: 'ElTable' }).vm;
    expect(table().expandedKeys).toEqual([]);
    await button('展开/折叠').trigger('click');
    await flushPromises();
    expect(table().expandedKeys).toEqual([1]);
    await button('展开/折叠').trigger('click');
    await flushPromises();
    expect(table().expandedKeys).toEqual([]);
    expect(wrapper.getComponent({ name: 'ElTable' }).vm).toBe(instance);
    expect(api.listMenu).toHaveBeenCalledTimes(1);
    expect((await api.listMenu.mock.results[0].value).items[0]).not.toHaveProperty('children');
    await wrapper.get('tbody [data-zx-action-id="add-child"]').trigger('click');
    expect(api.open).toHaveBeenCalledWith({ parentId: 1 });
  });
});
