import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { createPinia } from 'pinia';
import ElementPlus from 'element-plus';
import { createShortcutRuntime } from '@zxio/keybindings';
import { createShortcutPlugin } from '@zxio/keybindings/vue';
import { VueQueryPlugin } from '@tanstack/vue-query';
import type { TableRenderInstance } from '@zxio/table-render/ui';
import RolePage from '@/views/system/role/index.vue';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';

const api = vi.hoisted(() => ({
  listRole: vi.fn(),
  changeRoleStatus: vi.fn(),
  delRole: vi.fn(),
  confirm: vi.fn(),
  download: vi.fn(),
  navigate: vi.fn(),
  permission: vi.fn(),
  openEditor: vi.fn(),
  actionConfirm: vi.fn(),
  message: vi.fn(),
}));
vi.mock('@/api/system/role', () => api);
vi.mock('@/utils/permission', () => ({ checkPermi: api.permission }));
vi.mock('vue-router', () => ({ useRouter: () => ({ push: api.navigate }) }));
vi.mock('@zxio/zxui/theme-provider', async (original) => ({
  ...(await original<object>()),
  useThemeFeedback: () => ({
    ok: true,
    value: { confirm: api.actionConfirm, message: api.message },
  }),
}));
vi.mock('@/views/system/role/components/RoleFormDrawer.vue', () => ({
  default: {
    setup(_: unknown, { expose }: { expose: (value: unknown) => void }) {
      expose({ open: api.openEditor });
      return () => null;
    },
  },
}));
vi.mock('@/views/system/role/components/RoleDataScopeDrawer.vue', () => ({
  default: { render: () => null },
}));
const mounted: ReturnType<typeof mount>[] = [];
let pinia = createPinia();
const result = (roleName = 'server') => ({
  items: [{ roleId: 20, roleName, roleKey: 'server', status: '0' }],
  total: 31,
  page: 1,
  pageSize: 10,
});
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { resolve, promise };
}
function page() {
  const wrapper = mount(RolePage, {
    global: {
      plugins: [
        pinia,
        ElementPlus,
        [VueQueryPlugin, { queryClient }],
        createShortcutPlugin(createShortcutRuntime({ appId: 'role-page-test', platform: 'mac' })),
      ],
      config: {
        globalProperties: { $modal: { confirm: api.confirm }, download: api.download } as never,
      },
      stubs: { ZxContentWrap: { template: '<section><slot /></section>' }, DictSelect: true },
    },
  });
  mounted.push(wrapper);
  const grid = () => wrapper.getComponent({ name: 'ZxTableRender' });
  const table = () =>
    grid().vm as unknown as TableRenderInstance<
      never,
      { roleId: number },
      { roleName?: string; roleKey?: string; status?: string; dateRange?: string[] }
    >;
  const button = (label: string) =>
    wrapper.findAll('button').find((node) => node.text().trim() === label)!;
  return { wrapper, grid, table, button };
}
beforeEach(() => {
  vi.resetAllMocks();
  pinia = createPinia();
  queryClient.clear();
  setQuerySession(1, ['admin'], ['*:*:*']);
  api.listRole.mockResolvedValue(result());
  api.permission.mockReturnValue(true);
  api.changeRoleStatus.mockResolvedValue({});
  api.delRole.mockResolvedValue({});
  api.confirm.mockResolvedValue(undefined);
  api.openEditor.mockResolvedValue(undefined);
  api.actionConfirm.mockResolvedValue({ ok: true, value: 'confirm' });
});
afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
});

describe('role list with real TableRender and Vue Query', () => {
  it('keeps row action identity tied to role IDs after refresh', async () => {
    api.listRole.mockResolvedValue({
      ...result(),
      items: [{ roleId: 82, roleName: '角色82', roleKey: '82', status: '0' }],
    });
    const { wrapper, table } = page();
    await flushPromises();
    const old = wrapper.get('tbody [data-zx-action-id="edit"]').element;
    api.listRole.mockResolvedValue({
      ...result(),
      items: [{ roleId: 85, roleName: '角色85', roleKey: '85', status: '0' }],
    });
    await table().reload();
    await flushPromises();
    const edit = wrapper.get('tbody [data-zx-action-id="edit"]');
    expect(edit.element).not.toBe(old);
    expect(wrapper.element.contains(old)).toBe(false);
    await edit.trigger('click');
    expect(api.openEditor).toHaveBeenCalledWith(85);
  });
  it('pages and exports submitted filters, preserving an unsent draft', async () => {
    const { table, button } = page();
    await flushPromises();
    table().setDraft({
      roleName: ' selected ',
      roleKey: ' key ',
      status: '1',
      dateRange: ['2026-10-01', '2026-10-17'],
    });
    await flushPromises();
    await table().search();
    await flushPromises();
    await table().requery({ page: 3 });
    await flushPromises();
    const filters = {
      roleName: 'selected',
      roleKey: 'key',
      status: '1',
      beginTime: '2026-10-01',
      endTime: '2026-10-17',
    };
    expect(api.listRole.mock.calls.at(-1)?.[0]).toEqual({ ...filters, page: 3, pageSize: 10 });
    table().setDraft({ roleName: 'unsent' });
    await flushPromises();
    await button('导出').trigger('click');
    expect(api.download).toHaveBeenLastCalledWith(
      'system/role/export',
      filters,
      expect.any(String)
    );
    await table().search();
    await flushPromises();
    expect(api.listRole.mock.calls.at(-1)?.[0]).toMatchObject({ roleName: 'unsent', page: 1 });
  });
  it('retries initial/refresh failures and retains rows only for the same query key', async () => {
    api.listRole.mockRejectedValue(new Error('failed'));
    const { grid, table } = page();
    await flushPromises();
    expect(grid().props('status').error).toBeTruthy();
    api.listRole.mockResolvedValue(result());
    await table().reload();
    await flushPromises();
    expect(grid().props('rows')[0].roleName).toBe('server');
    api.listRole.mockRejectedValue(new Error('refresh failed'));
    await table().reload();
    await flushPromises();
    expect(grid().props('status').error).toBeTruthy();
    expect(grid().props('rows')[0].roleName).toBe('server');
    table().setDraft({ roleName: 'other' });
    await flushPromises();
    await table().search();
    await flushPromises();
    expect(grid().props('rows')).toEqual([]);
  });
  it('ignores an older request that resolves after the latest search', async () => {
    const { grid, table } = page();
    await flushPromises();
    const old = deferred<ReturnType<typeof result>>();
    api.listRole.mockReturnValueOnce(old.promise).mockResolvedValueOnce(result('new'));
    table().setDraft({ roleName: 'old' });
    await flushPromises();
    await table().search();
    await flushPromises();
    table().setDraft({ roleName: 'new' });
    await flushPromises();
    await table().search();
    await flushPromises();
    old.resolve(result('old'));
    await flushPromises();
    expect(grid().props('rows')[0].roleName).toBe('new');
    expect(table().displayed?.input.query).toEqual({ roleName: 'new' });
  });
  it('locks status by ID without mutating rows and discards confirmation after domain change', async () => {
    const { wrapper, grid } = page();
    await flushPromises();
    const row = Object.freeze(grid().props('rows')[0]);
    const confirmed = deferred<void>();
    api.confirm.mockReturnValue(confirmed.promise);
    const toggle = wrapper.getComponent({ name: 'ElSwitch' });
    toggle.vm.$emit('change', '1');
    toggle.vm.$emit('change', '1');
    await flushPromises();
    expect(api.confirm).toHaveBeenCalledTimes(1);
    expect(row.status).toBe('0');
    setQuerySession(3, [], []);
    confirmed.resolve();
    await flushPromises();
    expect(api.changeRoleStatus).not.toHaveBeenCalled();
  });
  it('protects administrator selection/status and rechecks permission after delete confirmation', async () => {
    api.listRole.mockResolvedValue({
      ...result(),
      items: [{ roleId: 1, roleName: 'admin', status: '0' }, ...result().items],
    });
    const { wrapper, table, button } = page();
    await flushPromises();
    expect(wrapper.findAllComponents({ name: 'ElSwitch' })[0].props('disabled')).toBe(true);
    await wrapper.get('thead input[type="checkbox"]').setValue(true);
    expect(table().selection.keys).toEqual([20]);
    const confirm = deferred<{ ok: true; value: 'confirm' }>();
    api.actionConfirm.mockReturnValue(confirm.promise);
    await button('删除').trigger('click');
    api.permission.mockReturnValue(false);
    confirm.resolve({ ok: true, value: 'confirm' });
    await flushPromises();
    expect(api.delRole).not.toHaveBeenCalled();
  });
  it('restores submitted navigation filters/page and not an unsent draft', async () => {
    const before = page();
    await flushPromises();
    before.table().setDraft({ roleName: 'selected' });
    await flushPromises();
    await before.table().search();
    await flushPromises();
    await before.table().requery({ page: 2 });
    await flushPromises();
    before.table().setDraft({ roleName: 'unsent' });
    await flushPromises();
    await before.wrapper.get('tbody [data-zx-action-id="auth-user"]').trigger('click');
    expect(api.navigate).toHaveBeenCalledWith('/system/role-auth/user/20');
    before.wrapper.unmount();
    const after = page();
    await flushPromises();
    expect(after.table().draft.roleName).toBe('selected');
    expect(after.table().applied?.pager?.page).toBe(2);
  });
});
