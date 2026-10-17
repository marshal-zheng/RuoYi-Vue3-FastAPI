import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as vue from 'vue';
import { defineComponent, h, onMounted, type App } from 'vue';
import { createPinia } from 'pinia';
import { flushPromises, mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { ElTable, ElTableColumn } from 'element-plus';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import RolePage from '@/views/system/role/index.vue';

const api = vi.hoisted(() => ({
  listRole: vi.fn(),
  changeRoleStatus: vi.fn(),
  delRole: vi.fn(),
  confirm: vi.fn(),
  download: vi.fn(),
  navigate: vi.fn(),
  permission: vi.fn(),
  openEditor: vi.fn(),
}));
vi.mock('@/api/system/role', () => api);
vi.mock('@/utils/permission', () => ({ checkPermi: api.permission }));
vi.mock('vue-router', () => ({ useRouter: () => ({ push: api.navigate }) }));
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
const Layout = defineComponent({
  setup(_, { slots }) {
    return () =>
      h(
        'section',
        Object.values(slots).map((slot) => slot?.())
      );
  },
});
const Grid = defineComponent({
  props: ['mode', 'rows', 'pagination', 'status', 'loadData'],
  emits: ['refresh', 'page-change'],
  setup(props, { slots }) {
    onMounted(() => props.loadData?.({ query: {}, pager: { page: 1, size: 10 } }));
    return () => h('section', slots.form?.({ query: {}, loading: false }));
  },
});
const TableGrid = defineComponent({
  props: ['mode', 'rows', 'pagination', 'status'],
  emits: ['refresh', 'page-change'],
  setup(props, { slots }) {
    return () =>
      h('section', slots.table?.({ grid: { list: props.rows }, renderEmpty: () => null }));
  },
});
const Button = defineComponent({
  emits: ['click'],
  setup(_, { emit, slots }) {
    return () =>
      h('button', { onClick: (event: MouseEvent) => emit('click', event) }, slots.default?.());
  },
});
let pinia = createPinia();
const mounted: ReturnType<typeof mount>[] = [];
function page({ realTable = false } = {}) {
  const wrapper = mount(RolePage, {
    global: {
      plugins: [
        pinia,
        [VueQueryPlugin, { queryClient }],
        (app: App) => {
          app.config.globalProperties.$modal = { confirm: api.confirm } as any;
          app.config.globalProperties.download = api.download;
        },
      ],
      directives: { hasPermi: () => {}, loading: () => {} },
      stubs: {
        ZxContentWrap: Layout,
        ZxListToolbar: Layout,
        ZxGridList: realTable ? TableGrid : Grid,
        ZxButton: realTable ? Button : true,
        ZxInput: true,
        ZxSearch: true,
        DictSelect: true,
        ElDatePicker: true,
        ElTable: realTable ? ElTable : true,
        ElTableColumn: realTable ? ElTableColumn : true,
        ElSwitch: true,
        ZxMoreAction: true,
      },
    },
  });
  mounted.push(wrapper);
  return {
    wrapper,
    state: wrapper.vm as unknown as Record<string, any>,
    grid: () => wrapper.findComponent(Grid),
  };
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => (resolve = done));
  return { resolve, promise };
}
const result = (roleName = 'server') => ({
  items: [{ roleId: 20, roleName, roleKey: 'server', status: '0' }],
  total: 31,
  page: 1,
  pageSize: 10,
});
beforeEach(() => {
  vi.resetAllMocks();
  pinia = createPinia();
  queryClient.clear();
  setQuerySession(1, ['admin'], ['*:*:*']);
  api.listRole.mockResolvedValue(result());
  api.permission.mockReturnValue(true);
  api.changeRoleStatus.mockResolvedValue({});
  api.confirm.mockResolvedValue(undefined);
  api.openEditor.mockResolvedValue(undefined);
  for (const key of ['ref', 'getCurrentInstance']) vi.stubGlobal(key, vue[key as keyof typeof vue]);
  vi.stubGlobal('useRouter', () => ({ push: api.navigate }));
});
afterEach(() => {
  mounted.splice(0).forEach((w) => w.unmount());
  endQuerySession();
  queryClient.clear();
  vi.unstubAllGlobals();
});

describe('role list resource ownership', () => {
  it('replaces action nodes when a refresh puts a different role at the same row index', async () => {
    api.listRole.mockResolvedValue({
      ...result(),
      items: [{ roleId: 82, roleName: '角色 82', roleKey: 'role82', status: '0' }],
    });
    const { wrapper, state } = page({ realTable: true });
    await flushPromises();
    const oldRow = wrapper.get('tbody tr');
    const oldEdit = oldRow.findAll('button').find((button) => button.text() === '修改')!;
    expect(oldRow.text()).toContain('角色 82');

    api.listRole.mockResolvedValue({
      ...result(),
      items: [{ roleId: 85, roleName: '角色 85', roleKey: 'role85', status: '0' }],
    });
    state.refreshList();
    await flushPromises();

    const newRow = wrapper.get('tbody tr');
    const newEdit = newRow.findAll('button').find((button) => button.text() === '修改')!;
    expect(newRow.text()).toContain('角色 85');
    // A pointer/focus held on 82's action must not become an action on role 85.
    expect(newEdit.element).not.toBe(oldEdit.element);
    expect(wrapper.element.contains(oldEdit.element)).toBe(false);
    await newEdit.trigger('click');
    expect(api.openEditor).toHaveBeenCalledWith(85);
  });

  it('uses submitted filters for paging/export and resets a new search to page one', async () => {
    const { state, grid } = page();
    await flushPromises();
    expect(grid().props('mode')).toBe('controlled');
    Object.assign(state.draft, {
      roleName: ' selected ',
      roleKey: ' key ',
      status: '1',
      dateRange: ['2026-10-01', '2026-10-17'],
    });
    state.onSearch();
    await flushPromises();
    grid().vm.$emit('page-change', { page: 3, size: 10 });
    await flushPromises();
    const filters = {
      roleName: 'selected',
      roleKey: 'key',
      status: '1',
      beginTime: '2026-10-01',
      endTime: '2026-10-17',
    };
    expect(api.listRole.mock.calls.at(-1)?.[0]).toEqual({
      ...filters,
      page: 3,
      pageSize: 10,
    });
    state.draft.roleName = 'unsent';
    state.handleExport();
    expect(api.download).toHaveBeenLastCalledWith(
      'system/role/export',
      filters,
      expect.any(String)
    );
    state.onSearch();
    await flushPromises();
    expect(grid().props('pagination').page).toBe(1);
    expect(api.listRole.mock.calls.at(-1)?.[0].roleName).toBe('unsent');
  });

  it('shows initial and refresh failures with retry while retaining only same-key rows', async () => {
    api.listRole.mockRejectedValue(new Error('failed'));
    const { grid, state } = page();
    await flushPromises();
    expect(grid().props('status')?.error).toBeTruthy();
    api.listRole.mockResolvedValue(result());
    grid().vm.$emit('refresh');
    await flushPromises();
    expect(grid().props('rows')[0].roleName).toBe('server');
    api.listRole.mockRejectedValue(new Error('refresh failed'));
    grid().vm.$emit('refresh');
    await flushPromises();
    expect(grid().props('status').error).toBeTruthy();
    expect(grid().props('rows')[0].roleName).toBe('server');
    state.draft.roleName = 'other';
    state.onSearch();
    await flushPromises();
    expect(grid().props('rows')).toEqual([]);
  });

  it('keeps latest search result when an earlier request resolves last', async () => {
    const { grid, state } = page();
    await flushPromises();
    const old = deferred<ReturnType<typeof result>>();
    api.listRole.mockReturnValueOnce(old.promise).mockResolvedValueOnce(result('new'));
    state.draft.roleName = 'old';
    state.onSearch();
    await flushPromises();
    state.draft.roleName = 'new';
    state.onSearch();
    await flushPromises();
    old.resolve(result('old'));
    await flushPromises();
    expect(grid().props('rows')[0].roleName).toBe('new');
  });

  it('locks status by role ID and captures the target without mutating cached rows', async () => {
    const { grid, state } = page();
    await flushPromises();
    const row = Object.freeze(grid().props('rows')[0]);
    const confirmed = deferred<void>();
    api.confirm.mockReturnValue(confirmed.promise);
    const saving = state.handleStatusChange('1', row);
    state.handleStatusChange('1', { ...row });
    await flushPromises();
    expect(api.confirm).toHaveBeenCalledTimes(1);
    expect(row.status).toBe('0');
    confirmed.resolve();
    await saving;
    await flushPromises();
    expect(api.changeRoleStatus.mock.calls[0].slice(0, 2)).toEqual([20, '1']);
  });

  it('does not offer status writes for the administrator role or without edit permission', async () => {
    const { state } = page();
    await flushPromises();
    await state.handleStatusChange('1', { roleId: 1, status: '0' });
    api.permission.mockReturnValue(false);
    await state.handleStatusChange('1', { roleId: 20, status: '0' });
    expect(api.confirm).not.toHaveBeenCalled();
    expect(api.changeRoleStatus).not.toHaveBeenCalled();
  });

  it('restores only submitted list state after authorization and discards an expired confirmation', async () => {
    const before = page();
    await flushPromises();
    before.state.draft.roleName = 'selected';
    before.state.onSearch();
    await flushPromises();
    before.grid().vm.$emit('page-change', { page: 2, size: 10 });
    await flushPromises();
    before.state.draft.roleName = 'unsent';
    before.state.handleAuthUser({ roleId: 20 });
    expect(api.navigate).toHaveBeenCalledWith('/system/role-auth/user/20');
    before.wrapper.unmount();
    const after = page();
    await flushPromises();
    expect(after.state.draft.roleName).toBe('selected');
    expect(after.grid().props('pagination').page).toBe(2);
    const confirmed = deferred<void>();
    api.confirm.mockReturnValue(confirmed.promise);
    const saving = after.state.handleStatusChange('1', after.grid().props('rows')[0]);
    setQuerySession(3, [], []);
    confirmed.resolve();
    await saving;
    expect(api.changeRoleStatus).not.toHaveBeenCalled();
    expect(after.state.submitted).toEqual({});
  });
});
