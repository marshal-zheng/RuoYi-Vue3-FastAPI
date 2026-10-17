import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick, type App } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';
import { createPinia } from 'pinia';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import type { UserFilters } from '@/queries/system/user';
import UserPage from '@/views/system/user/index.vue';

interface UserPageState {
  draft: UserFilters & { dateRange: string[] | null };
  submitted: UserFilters;
  ids: number[];
  onSearch(): void;
  handleExport(): void;
  handleNodeClick(node: { id: number }): void;
  handleSelectionChange(rows: { userId: number }[]): void;
  handleAuthRole(row: { userId: number }): void;
  handleStatusChange(
    status: '0' | '1',
    row: { userId: number; status: '0' | '1' }
  ): Promise<void> | undefined;
}

const api = vi.hoisted(() => ({
  listUser: vi.fn(),
  deptTreeSelect: vi.fn(),
  changeUserStatus: vi.fn(),
  delUser: vi.fn(),
  resetUserPwd: vi.fn(),
  confirm: vi.fn(),
  download: vi.fn(),
  navigate: vi.fn(),
}));
vi.mock('@/api/system/user', () => api);
vi.mock('@/store/modules/app', () => ({
  default: () => ({ device: 'desktop' }),
}));
vi.mock('@/utils/permission', () => ({ checkPermi: () => true }));
vi.mock('vue-router', () => ({ useRouter: () => ({ push: api.navigate }) }));
vi.mock('@/views/system/user/components/UserFormDialog.vue', () => ({
  default: { render: () => null },
}));
vi.mock('@/views/system/user/components/UserImportDialog.vue', () => ({
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
  setup(_, { slots }) {
    return () => h('section', slots.form?.({ query: {}, loading: false }));
  },
});
const Tree = defineComponent({
  setup(_, { expose }) {
    expose({ filter: vi.fn(), setCurrentKey: vi.fn() });
    return () => h('div');
  },
});
const mounted: ReturnType<typeof mount>[] = [];
let pinia = createPinia();
function editor() {
  const wrapper = mount(UserPage, {
    global: {
      plugins: [
        pinia,
        [VueQueryPlugin, { queryClient }],
        (app: App) => {
          app.config.globalProperties.$modal = {
            confirm: api.confirm,
            alert: vi.fn(),
            alertError: vi.fn(),
            alertSuccess: vi.fn(),
            alertWarning: vi.fn(),
            prompt: vi.fn(),
            loading: vi.fn(),
            closeLoading: vi.fn(),
          };
          app.config.globalProperties.download = api.download;
        },
      ],
      directives: { hasPermi: () => {}, loading: () => {} },
      stubs: {
        ZxContentWrap: Layout,
        ZxSplitBox: Layout,
        ZxListToolbar: Layout,
        ZxGridList: Grid,
        ZxButton: true,
        ZxInput: true,
        ZxSearch: true,
        DictSelect: true,
        ElTree: Tree,
        ElDatePicker: true,
        ElTable: true,
        ElTableColumn: true,
        ElSwitch: true,
        ZxMoreAction: true,
      },
    },
  });
  mounted.push(wrapper);
  // Read production setup state; the test contains no duplicate filter or write implementation.
  const state = wrapper.vm as unknown as UserPageState;
  return { wrapper, state, grid: () => wrapper.findComponent(Grid) };
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => (resolve = done));
  return { promise, resolve };
}
const page = (name = 'server') => ({
  items: [{ userId: 2, userName: name, status: '0' }],
  total: 21,
  page: 1,
  pageSize: 10,
});
beforeEach(() => {
  vi.resetAllMocks();
  pinia = createPinia();
  endQuerySession();
  queryClient.clear();
  setQuerySession(1, ['admin'], ['system:user:list']);
  api.listUser.mockResolvedValue(page());
  api.deptTreeSelect.mockResolvedValue({ items: [] });
  api.changeUserStatus.mockResolvedValue({});
  api.delUser.mockResolvedValue(null);
});
afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
});

describe('user native query and submitted filter ownership', () => {
  it('refreshes when submitting the same filters and corrects a deleted last page only after its response', async () => {
    const { state, grid } = editor();
    await flushPromises();
    state.onSearch();
    await flushPromises();
    expect(api.listUser).toHaveBeenCalledTimes(2);
    const pending = deferred<ReturnType<typeof page>>();
    api.listUser.mockReturnValueOnce(pending.promise).mockResolvedValueOnce(page());
    grid().vm.$emit('page-change', { page: 3, size: 10 });
    await nextTick();
    expect(grid().props('pagination').page).toBe(3);
    pending.resolve({ ...page(), items: [], total: 20, page: 3 });
    await flushPromises();
    expect(grid().props('pagination').page).toBe(2);
    expect(api.listUser.mock.calls.at(-1)?.[0]).toEqual({ page: 2, pageSize: 10 });
    grid().vm.$emit('page-change', { page: 2, size: 50 });
    await flushPromises();
    expect(grid().props('pagination').page).toBe(1);
    expect(api.listUser.mock.calls.at(-1)?.[0]).toEqual({ page: 1, pageSize: 50 });
  });
  it('exports submitted filters while unsent draft edits do not change the list or export', async () => {
    const { state, grid } = editor();
    await flushPromises();
    expect(grid().props('mode')).toBe('controlled');
    expect(grid().props('loadData')).toBeUndefined();
    Object.assign(state.draft, {
      userName: 'filtered',
      phonenumber: '138',
      status: '1',
      dateRange: ['2025-10-01', '2025-10-31'],
    });
    state.handleNodeClick({ id: 103 });
    await flushPromises();
    const filters = {
      userName: 'filtered',
      phonenumber: '138',
      status: '1',
      deptId: 103,
      beginTime: '2025-10-01',
      endTime: '2025-10-31',
    };
    expect(api.listUser.mock.calls.at(-1)?.[0]).toEqual({
      ...filters,
      page: 1,
      pageSize: 10,
    });
    state.draft.userName = 'unsent';
    state.draft.dateRange = null;
    state.handleExport();
    expect(api.download).toHaveBeenLastCalledWith(
      'system/user/export',
      filters,
      expect.any(String)
    );
    grid().vm.$emit('page-change', { page: 2, size: 10 });
    await flushPromises();
    expect(api.listUser.mock.calls.at(-1)?.[0]).toEqual({
      ...filters,
      page: 2,
      pageSize: 10,
    });
    state.onSearch();
    await flushPromises();
    state.handleExport();
    expect(api.download.mock.calls.at(-1)?.[1]).toEqual({
      userName: 'unsent',
      phonenumber: '138',
      status: '1',
      deptId: 103,
    });
  });

  it('retains same-query rows on refresh failure and clears rows when filters change', async () => {
    const { state, grid } = editor();
    await flushPromises();
    api.listUser.mockRejectedValue(new Error('offline'));
    grid().vm.$emit('refresh');
    await flushPromises();
    expect(grid().props('rows')).toEqual(page().items);
    expect(grid().props('status').error).toBeTruthy();
    const pending = deferred<ReturnType<typeof page>>();
    api.listUser.mockReturnValue(pending.promise);
    state.draft.userName = 'new';
    state.onSearch();
    await nextTick();
    expect(grid().props('rows')).toEqual([]);
    expect(grid().props('status').loading).toBe(true);
    pending.resolve(page('new'));
    await flushPromises();
    expect(grid().props('rows')[0].userName).toBe('new');
  });

  it('locks status confirmation by user ID across background row replacement without mutating data', async () => {
    const { state, grid } = editor();
    await flushPromises();
    const first = grid().props('rows')[0];
    Object.freeze(first);
    const confirmation = deferred<void>();
    api.confirm.mockReturnValue(confirmation.promise);
    const oldTask = state.handleStatusChange('1', first);
    await flushPromises();
    expect(first.status).toBe('0');
    api.listUser.mockResolvedValue(page('refreshed'));
    grid().vm.$emit('refresh');
    await flushPromises();
    const replacement = grid().props('rows')[0];
    expect(replacement.userName).toBe('refreshed');
    state.handleStatusChange('1', replacement);
    await flushPromises();
    expect(api.confirm).toHaveBeenCalledTimes(1);
    expect(api.changeUserStatus).not.toHaveBeenCalled();
    confirmation.resolve();
    await oldTask;
    expect(api.changeUserStatus).toHaveBeenCalledTimes(1);
    expect(api.changeUserStatus.mock.calls[0].slice(0, 2)).toEqual([2, '1']);
    expect(first.status).toBe('0');
  });

  it('rejects an old confirmation after scope change and resets business filters and selection', async () => {
    const { state, grid } = editor();
    await flushPromises();
    const confirmation = deferred<void>();
    api.confirm.mockReturnValue(confirmation.promise);
    state.draft.userName = 'old-account';
    state.handleSelectionChange([{ userId: 2 }]);
    const task = state.handleStatusChange('1', grid().props('rows')[0]);
    await flushPromises();
    setQuerySession(3, [], []);
    await flushPromises();
    confirmation.resolve();
    await task;
    expect(api.changeUserStatus).not.toHaveBeenCalled();
    expect(state.ids).toEqual([]);
    expect(state.draft.userName).toBeUndefined();
    expect(api.listUser.mock.calls.at(-1)?.[0]).toEqual({
      page: 1,
      pageSize: 10,
    });
  });
});

describe('user authorization return state', () => {
  it('restores submitted filters and page after the list remounts, without restoring unsent edits', async () => {
    const before = editor();
    await flushPromises();
    Object.assign(before.state.draft, {
      userName: ' selected ',
      dateRange: ['2026-10-01', '2026-10-17'],
    });
    before.state.handleNodeClick({ id: 103 });
    await flushPromises();
    before.grid().vm.$emit('page-change', { page: 2, size: 10 });
    await flushPromises();
    before.state.draft.userName = 'unsent';
    before.state.handleAuthRole({ userId: 42 });
    expect(api.navigate).toHaveBeenCalledWith('/system/user-auth/role/42');
    before.wrapper.unmount();
    const after = editor();
    await flushPromises();
    expect(after.grid().props('pagination').page).toBe(2);
    expect(after.state.submitted).toEqual({
      userName: 'selected',
      deptId: 103,
      beginTime: '2026-10-01',
      endTime: '2026-10-17',
    });
    expect(after.state.draft.userName).toBe('selected');
    expect(after.state.draft.dateRange).toEqual(['2026-10-01', '2026-10-17']);
    after.state.handleExport();
    expect(api.download.mock.calls.at(-1)?.[1]).toEqual(after.state.submitted);
  });

  it('does not carry a previous session list snapshot into a new account', async () => {
    const before = editor();
    await flushPromises();
    before.state.draft.userName = 'old-scope';
    before.state.onSearch();
    before.state.handleAuthRole({ userId: 42 });
    before.wrapper.unmount();
    setQuerySession(9, [], []);
    const after = editor();
    await flushPromises();
    expect(after.state.submitted).toEqual({});
    expect(after.grid().props('pagination').page).toBe(1);
  });
});
