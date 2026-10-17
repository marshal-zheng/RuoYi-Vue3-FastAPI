import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import * as vue from 'vue';
import ElementPlus, { ElTable } from 'element-plus';
import { VueQueryPlugin, onlineManager } from '@tanstack/vue-query';
import { useRoute } from 'vue-router';
import { ZxGridList } from '@zxio/zxui';
import AuthRole from '@/views/system/user/authRole.vue';
import AuthUser from '@/views/system/role/authUser.vue';
import SelectUser from '@/views/system/role/selectUser.vue';
import { checkPermi, checkRole } from '@/utils/permission';
import { getAuthRole } from '@/api/system/user';
import { allocatedUserList, unallocatedUserList } from '@/api/system/role';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';

const api = vi.hoisted(() => ({
  assign: vi.fn(),
  grant: vi.fn(),
  revoke: vi.fn(),
  batch: vi.fn(),
}));
vi.mock('@/api/system/user', () => ({
  getAuthRole: vi.fn(),
  updateAuthRole: api.assign,
}));
vi.mock('@/api/system/role', () => ({
  allocatedUserList: vi.fn(),
  unallocatedUserList: vi.fn(),
  authUserSelectAll: api.grant,
  authUserCancel: api.revoke,
  authUserCancelAll: api.batch,
}));
vi.mock('vue-router', () => ({ useRoute: vi.fn() }));
vi.mock('@/utils/permission', () => ({
  checkPermi: vi.fn(() => true),
  checkRole: vi.fn(() => true),
}));
const mounted: ReturnType<typeof mount>[] = [];
const slots = {
  template:
    '<div><slot name="title" /><slot /><slot name="actions" /><slot name="filters" /><slot name="search" /><slot name="footer" /></div>',
};
const route = vue.reactive({ params: { userId: '42', roleId: '20' } });
const close = vi.fn();
function page(component: typeof AuthRole, props = {}) {
  const wrapper = mount(component, {
    props,
    global: {
      plugins: [ElementPlus, [VueQueryPlugin, { queryClient }]],
      components: { ZxGridList },
      directives: { hasPermi: () => {} },
      config: {
        globalProperties: {
          useDict: () => ({ sys_normal_disable: vue.ref([]) }),
          parseTime: () => '',
          $tab: { closeOpenPage: close },
          $modal: { confirm: vi.fn().mockResolvedValue(undefined) },
        } as never,
      },
      stubs: {
        ZxContentWrap: slots,
        ZxListToolbar: slots,
        ZxDialog: slots,
        ZxButton: {
          template: '<button @click="$emit(\'click\')"><slot /></button>',
        },
        ZxInput: true,
        ZxSearch: true,
        DictStatus: true,
        DictTag: true,
        SelectUser: component === SelectUser ? false : true,
      },
    },
  });
  mounted.push(wrapper);
  return wrapper;
}
interface PageState {
  show(): void;
  handleSave(): Promise<void>;
  handleSelectUser(): Promise<void>;
  cancelAuthUser(row: { userId: number }): Promise<void>;
  handleQuery(): void;
  onSearch(): void;
  visible: boolean;
  draft: { userName: string };
  queryParams: { userName: string };
  userIds: number[];
  writeError: string;
  protectedRoles: boolean;
}
function state(wrapper: ReturnType<typeof page>) {
  return (wrapper.vm as unknown as { $: { setupState: PageState } }).$.setupState;
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((accept) => {
    resolve = accept;
  });
  return { promise, resolve };
}
const roles = Array.from({ length: 12 }, (_, i) => ({
  roleId: i + 2,
  roleName: `role-${i + 2}`,
  roleKey: `key-${i}`,
  flag: i === 0 || i === 11,
}));
const users = (start: number, total = 23) => ({
  items: Array.from({ length: Math.min(10, total - start + 1) }, (_, i) => ({
    userId: start + i,
    userName: `user-${start + i}`,
  })),
  total,
  page: Math.ceil(start / 10),
  pageSize: 10,
});
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(checkPermi).mockReturnValue(true);
  vi.mocked(checkRole).mockReturnValue(true);
  queryClient.clear();
  setQuerySession(1, ['admin'], ['*:*:*']);
  onlineManager.setOnline(true);
  route.params.userId = '42';
  route.params.roleId = '20';
  vi.mocked(getAuthRole).mockResolvedValue({
    user: { userId: 42, userName: 'alice' },
    roles,
  } as never);
  vi.mocked(allocatedUserList).mockImplementation(
    async (input) =>
      users((Number(input?.page ?? 1) - 1) * Number(input?.pageSize ?? 10) + 1) as never
  );
  vi.mocked(unallocatedUserList).mockImplementation(
    async (input) =>
      users((Number(input?.page ?? 1) - 1) * Number(input?.pageSize ?? 10) + 1) as never
  );
  for (const fn of Object.values(api)) fn.mockResolvedValue(null);
  for (const key of ['ref', 'reactive', 'computed', 'getCurrentInstance', 'nextTick'])
    vi.stubGlobal(key, vue[key as keyof typeof vue]);
  vi.mocked(useRoute).mockReturnValue(route as never);
});
afterEach(() => {
  mounted.splice(0).forEach((w) => w.unmount());
  endQuerySession();
  queryClient.clear();
  onlineManager.setOnline(true);
});

it('mounts a real GridList and table with only one initial user-role request', async () => {
  const wrapper = page(AuthRole);
  await flushPromises();
  expect(wrapper.findComponent(ZxGridList).exists()).toBe(true);
  expect(wrapper.findComponent(ElTable).exists()).toBe(true);
  expect(getAuthRole).toHaveBeenCalledTimes(1);
});
it('allocated page 2 sends the actual pager and exposes the total', async () => {
  const wrapper = page(AuthUser);
  await flushPromises();
  wrapper.findComponent(ZxGridList).vm.$emit('page-change', { page: 2, size: 10 });
  await flushPromises();
  expect(vi.mocked(allocatedUserList).mock.calls.at(-1)?.[0]).toMatchObject({
    roleId: 20,
    page: 2,
    pageSize: 10,
  });
  expect(wrapper.findComponent(ElTable).props('data')?.[0]?.userId).toBe(11);
  expect(wrapper.findComponent(ZxGridList).props('pagination')).toMatchObject({
    total: 23,
  });
});
it('initializes all assigned roles and preserves a deselection when returning to page 1', async () => {
  const wrapper = page(AuthRole);
  await flushPromises();
  const table = wrapper.findComponent(ElTable);
  await table.findAll('tbody input[type=checkbox]')[0]!.setValue(false);
  await flushPromises();
  wrapper.findComponent(ZxGridList).vm.$emit('page-change', { page: 2, size: 10 });
  await flushPromises();
  expect(table.props('data')?.[0]?.roleId).toBe(12);
  wrapper.findComponent(ZxGridList).vm.$emit('page-change', { page: 1, size: 10 });
  await flushPromises();
  expect(table.vm.getSelectionRows().map((row: { roleId: number }) => row.roleId)).not.toContain(2);
  await state(wrapper).handleSave();
  expect(api.assign.mock.calls.at(-1)?.[0]).toEqual({
    userId: 42,
    roleIds: [13],
  });
});
it('selector keeps selections across pages and sends one incremental relation array', async () => {
  const wrapper = page(SelectUser, { roleId: '20' });
  state(wrapper).show();
  await flushPromises();
  const table = wrapper.findComponent(ElTable);
  await table.findAll('tbody input[type=checkbox]')[1]!.setValue(true);
  await flushPromises();
  const grid = wrapper.findComponent(ZxGridList);
  expect(grid.exists()).toBe(true);
  grid.vm.$emit('page-change', { page: 2, size: 10 });
  await flushPromises();
  await table.findAll('tbody input[type=checkbox]')[1]!.setValue(true);
  await flushPromises();
  await state(wrapper).handleSelectUser();
  expect(api.grant.mock.calls.at(-1)?.[0]).toEqual({
    roleId: 20,
    userIds: [2, 12],
  });
});
it('selector shows the newest search and never lets an older response replace it', async () => {
  const old = deferred<ReturnType<typeof users>>();
  const latest = deferred<ReturnType<typeof users>>();
  vi.mocked(unallocatedUserList)
    .mockReturnValueOnce(old.promise)
    .mockReturnValueOnce(latest.promise);
  const wrapper = page(SelectUser, { roleId: '20' });
  state(wrapper).show();
  await flushPromises();
  state(wrapper).queryParams.userName = 'latest';
  state(wrapper).handleQuery();
  await flushPromises();
  latest.resolve(users(20));
  await flushPromises();
  old.resolve(users(1));
  await flushPromises();
  expect(wrapper.findComponent(ElTable).props('data')?.[0]?.userId).toBe(20);
});

it('keeps draft filter edits local and resets an allocated search to page 1', async () => {
  const wrapper = page(AuthUser);
  await flushPromises();
  wrapper.findComponent(ZxGridList).vm.$emit('page-change', { page: 2, size: 10 });
  await flushPromises();
  const before = vi.mocked(allocatedUserList).mock.calls.length;
  state(wrapper).draft.userName = '  newest  ';
  await vue.nextTick();
  expect(allocatedUserList).toHaveBeenCalledTimes(before);
  state(wrapper).onSearch();
  await flushPromises();
  expect(vi.mocked(allocatedUserList).mock.calls.at(-1)?.[0]).toMatchObject({
    page: 1,
    pageSize: 10,
    userName: 'newest',
  });
});
it('recovers a failed first role read and keeps edited selection through background refresh', async () => {
  vi.mocked(getAuthRole).mockRejectedValueOnce(new Error('read failed'));
  const wrapper = page(AuthRole);
  await flushPromises();
  const grid = wrapper.findComponent(ZxGridList);
  expect(grid.props('status')).toMatchObject({
    error: expect.objectContaining({ message: 'read failed' }),
  });
  await state(wrapper).handleSave();
  expect(api.assign).not.toHaveBeenCalled();
  grid.vm.$emit('refresh');
  await flushPromises();
  const table = wrapper.findComponent(ElTable);
  await table.findAll('tbody input[type=checkbox]')[0]!.setValue(false);
  await flushPromises();
  vi.mocked(getAuthRole).mockResolvedValueOnce({
    user: { userId: 42 },
    roles: roles.map((row) => ({ ...row, flag: true })),
  } as never);
  grid.vm.$emit('refresh');
  await flushPromises();
  await state(wrapper).handleSave();
  expect(api.assign.mock.calls.at(-1)?.[0]).toEqual({
    userId: 42,
    roleIds: [13],
  });
});
it('keeps allocated rows and shows refresh failure, then exposes paused reads separately', async () => {
  const wrapper = page(AuthUser);
  await flushPromises();
  vi.mocked(allocatedUserList).mockRejectedValueOnce(new Error('refresh failed'));
  const grid = wrapper.findComponent(ZxGridList);
  grid.vm.$emit('refresh');
  await flushPromises();
  expect(wrapper.findComponent(ElTable).props('data')).toHaveLength(10);
  expect(grid.props('status')).toMatchObject({
    error: expect.objectContaining({ message: 'refresh failed' }),
    loading: false,
  });
  onlineManager.setOnline(false);
  state(wrapper).draft.userName = 'offline';
  state(wrapper).onSearch();
  await flushPromises();
  expect(grid.props('status')).toMatchObject({ paused: true });
});
it('selector retries a failed read and keeps selection when a later page fails', async () => {
  vi.mocked(unallocatedUserList).mockRejectedValueOnce(new Error('unavailable'));
  const wrapper = page(SelectUser, { roleId: '20' });
  state(wrapper).show();
  await flushPromises();
  const grid = wrapper.findComponent(ZxGridList);
  expect(grid.props('status')).toMatchObject({ error: expect.any(Error) });
  grid.vm.$emit('refresh');
  await flushPromises();
  const table = wrapper.findComponent(ElTable);
  await table.findAll('tbody input[type=checkbox]')[1]!.setValue(true);
  await flushPromises();
  vi.mocked(unallocatedUserList).mockRejectedValueOnce(new Error('page failed'));
  grid.vm.$emit('page-change', { page: 2, size: 10 });
  await flushPromises();
  expect(state(wrapper).userIds).toEqual([2]);
  grid.vm.$emit('refresh');
  await flushPromises();
  await state(wrapper).handleSelectUser();
  expect(api.grant.mock.calls.at(-1)?.[0]).toEqual({
    roleId: 20,
    userIds: [2],
  });
});
it('resets selection and filters on reopen and ignores a previous opening response', async () => {
  const old = deferred<ReturnType<typeof users>>();
  vi.mocked(unallocatedUserList).mockReturnValueOnce(old.promise);
  const wrapper = page(SelectUser, { roleId: '20' });
  state(wrapper).show();
  await flushPromises();
  state(wrapper).queryParams.userName = 'old';
  state(wrapper).visible = false;
  await flushPromises();
  vi.mocked(unallocatedUserList).mockResolvedValueOnce(users(20));
  state(wrapper).show();
  await flushPromises();
  old.resolve(users(1));
  await flushPromises();
  expect(state(wrapper).queryParams.userName).toBe('');
  expect(state(wrapper).userIds).toEqual([]);
  expect(wrapper.findComponent(ElTable).props('data')?.[0]?.userId).toBe(20);
});
it('does not close a reopened selector when a previous opening write completes', async () => {
  const write = deferred<null>();
  api.grant.mockReturnValueOnce(write.promise);
  const wrapper = page(SelectUser, { roleId: '20' });
  state(wrapper).show();
  await flushPromises();
  const table = wrapper.findComponent(ElTable);
  await table.findAll('tbody input[type=checkbox]')[1]!.setValue(true);
  await flushPromises();
  const task = state(wrapper).handleSelectUser();
  await flushPromises();
  state(wrapper).visible = false;
  await flushPromises();
  state(wrapper).show();
  await flushPromises();
  write.resolve(null);
  await task;
  await flushPromises();
  expect(state(wrapper).visible).toBe(true);
  expect(wrapper.emitted('ok')).toBeUndefined();
});
it('does not report successful authorization as failed when the invalidated read fails', async () => {
  const wrapper = page(AuthRole);
  await flushPromises();
  vi.mocked(getAuthRole).mockRejectedValueOnce(new Error('read after write failed'));
  await state(wrapper).handleSave();
  await flushPromises();
  expect(api.assign).toHaveBeenCalledTimes(1);
  expect(close).toHaveBeenCalledTimes(1);
  expect(state(wrapper).writeError).toBe('');
});
it('preserves role selection on write failure and retries the explicit empty replacement', async () => {
  vi.mocked(getAuthRole).mockResolvedValueOnce({
    user: { userId: 42 },
    roles: [{ roleId: 20, flag: true }],
  } as never);
  const wrapper = page(AuthRole);
  await flushPromises();
  const table = wrapper.findComponent(ElTable);
  await table.findAll('tbody input[type=checkbox]')[0]!.setValue(false);
  await flushPromises();
  api.assign.mockRejectedValueOnce(new Error('write failed'));
  await state(wrapper).handleSave();
  await flushPromises();
  expect(state(wrapper).writeError).toContain('保存失败');
  expect(close).not.toHaveBeenCalled();
  await state(wrapper).handleSave();
  expect(api.assign.mock.calls.at(-1)?.[0]).toEqual({
    userId: 42,
    roleIds: [],
  });
});
it('preserves assigned inactive/admin roles and prevents nonadmin replacement of protected assignments', async () => {
  vi.mocked(getAuthRole).mockResolvedValueOnce({
    user: { userId: 42 },
    roles: [
      { roleId: 1, flag: true },
      { roleId: 20, status: '1', flag: true },
    ],
  } as never);
  const wrapper = page(AuthRole);
  await flushPromises();
  await state(wrapper).handleSave();
  expect(api.assign.mock.calls.at(-1)?.[0]).toEqual({
    userId: 42,
    roleIds: [1, 20],
  });
  await flushPromises();
  setQuerySession(99, [], ['*:*:*']);
  vi.mocked(getAuthRole).mockResolvedValueOnce({
    user: { userId: 43 },
    roles: [{ roleId: 1, flag: true }],
  } as never);
  route.params.userId = '43';
  await flushPromises();
  vi.mocked(getAuthRole).mockResolvedValue({
    user: { userId: 43 },
    roles: [{ roleId: 1, flag: true }],
  } as never);
  const protectedEditor = page(AuthRole);
  await flushPromises();
  expect(state(protectedEditor).protectedRoles).toBe(true);
  await state(protectedEditor).handleSave();
  expect(api.assign).toHaveBeenCalledTimes(1);
});
it('does not permit writes without edit permission or for the administrator user', async () => {
  vi.mocked(checkPermi).mockReturnValue(false);
  const allocated = page(AuthUser);
  await flushPromises();
  await state(allocated).cancelAuthUser({ userId: 42 });
  expect(api.revoke).not.toHaveBeenCalled();
  const editor = page(AuthRole);
  await flushPromises();
  await state(editor).handleSave();
  expect(api.assign).not.toHaveBeenCalled();
  vi.mocked(checkPermi).mockReturnValue(true);
  vi.mocked(getAuthRole).mockResolvedValueOnce({
    user: { userId: 1 },
    roles,
  } as never);
  route.params.userId = '1';
  await flushPromises();
  await state(editor).handleSave();
  expect(api.assign).not.toHaveBeenCalled();
});
it('clears role draft and suppresses writes when the session changes', async () => {
  const wrapper = page(AuthRole);
  await flushPromises();
  setQuerySession(2, ['admin'], ['*:*:*']);
  await flushPromises();
  expect(wrapper.findComponent(ElTable).props('data')).toEqual([]);
  await state(wrapper).handleSave();
  expect(api.assign).not.toHaveBeenCalled();
});

it('isolates role editor reads when the target route changes during a request', async () => {
  const old = deferred<unknown>();
  vi.mocked(getAuthRole).mockReturnValueOnce(old.promise as never);
  const wrapper = page(AuthRole);
  await flushPromises();
  vi.mocked(getAuthRole).mockResolvedValueOnce({
    user: { userId: 43 },
    roles: [{ roleId: 30, flag: true }],
  } as never);
  route.params.userId = '43';
  await flushPromises();
  old.resolve({ user: { userId: 42 }, roles });
  await flushPromises();
  await state(wrapper).handleSave();
  expect(api.assign.mock.calls.at(-1)?.[0]).toEqual({ userId: 43, roleIds: [30] });
});
it('retains selected users through a different search and closes on role identity change', async () => {
  const wrapper = page(SelectUser, { roleId: '20' });
  state(wrapper).show();
  await flushPromises();
  const table = wrapper.findComponent(ElTable);
  await table.findAll('tbody input[type=checkbox]')[1]!.setValue(true);
  await flushPromises();
  vi.mocked(unallocatedUserList).mockResolvedValueOnce(users(20));
  state(wrapper).queryParams.userName = 'other';
  state(wrapper).handleQuery();
  await flushPromises();
  await table.findAll('tbody input[type=checkbox]')[0]!.setValue(true);
  await flushPromises();
  expect(state(wrapper).userIds).toEqual([2, 20]);
  await wrapper.setProps({ roleId: '30' } as never);
  await flushPromises();
  expect(state(wrapper).visible).toBe(false);
  expect(state(wrapper).userIds).toEqual([]);
  await state(wrapper).handleSelectUser();
  expect(api.grant).not.toHaveBeenCalled();
});

it('does not let a non-root account with the admin role revoke administrator-role users', async () => {
  setQuerySession(99, ['admin'], ['*:*:*']);
  route.params.roleId = '1';
  const wrapper = page(AuthUser);
  await flushPromises();
  await state(wrapper).cancelAuthUser({ userId: 42 });
  expect(api.revoke).not.toHaveBeenCalled();
  expect(
    (
      wrapper.findComponent(ElTable).findAll('tbody input[type=checkbox]')[1]!
        .element as HTMLInputElement
    ).disabled
  ).toBe(true);
});
it('does not let a non-root account with the admin role grant administrator-role users', async () => {
  setQuerySession(99, ['admin'], ['*:*:*']);
  const wrapper = page(SelectUser, { roleId: '1' });
  state(wrapper).show();
  await flushPromises();
  state(wrapper).userIds = [42];
  await state(wrapper).handleSelectUser();
  expect(api.grant).not.toHaveBeenCalled();
  expect(
    (
      wrapper.findComponent(ElTable).findAll('tbody input[type=checkbox]')[1]!
        .element as HTMLInputElement
    ).disabled
  ).toBe(true);
});
it('explains and blocks protected replacement for a non-root account with the admin role', async () => {
  setQuerySession(99, ['admin'], ['*:*:*']);
  vi.mocked(getAuthRole).mockResolvedValue({
    user: { userId: 42 },
    roles: [{ roleId: 1, flag: true }],
  } as never);
  const wrapper = page(AuthRole);
  await flushPromises();
  expect(state(wrapper).protectedRoles).toBe(true);
  expect(wrapper.text()).toContain('该用户包含管理员角色，需要管理员调整授权');
  await state(wrapper).handleSave();
  expect(api.assign).not.toHaveBeenCalled();
});
