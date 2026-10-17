import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  MutationObserver,
  onlineManager,
  useQuery,
  VueQueryPlugin,
  skipToken,
} from '@tanstack/vue-query';
import { defineComponent, unref } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';
import { isQueryRequest } from '@zxio/http';
import * as api from '@/api/system/user';
import * as roleApi from '@/api/system/role';
import { queryClient } from '../client';
import { endQuerySession, setQuerySession } from '../context';
import * as userDomain from './user';
import { userDeptTreeOptions } from './dept';

vi.mock('@/api/system/user', () => ({
  listUser: vi.fn(),
  getUser: vi.fn(),
  deptTreeSelect: vi.fn(),
  addUser: vi.fn(),
  updateUser: vi.fn(),
  delUser: vi.fn(),
  changeUserStatus: vi.fn(),
  resetUserPwd: vi.fn(),
  updateAuthRole: vi.fn(),
  getAuthRole: vi.fn(),
  updateUserProfile: vi.fn(),
  updateUserPwd: vi.fn(),
  uploadAvatar: vi.fn(),
  importUserExcel: vi.fn(),
}));
vi.mock('@/api/system/role', () => ({
  allocatedUserList: vi.fn(),
  unallocatedUserList: vi.fn(),
  authUserCancel: vi.fn(),
  authUserCancelAll: vi.fn(),
  authUserSelectAll: vi.fn(),
}));
function domain() {
  return userDomain;
}
const wrappers: ReturnType<typeof mount>[] = [];
const page = (userName = 'before') => ({
  items: [{ userId: 7, userName, status: '0' as const }],
  total: 1,
  page: 1,
  pageSize: 10,
});
const detail = () => ({
  data: page().items[0],
  posts: [],
  roles: [],
  postIds: [3],
  roleIds: [2],
});
beforeEach(() => {
  endQuerySession();
  queryClient.clear();
  vi.resetAllMocks();
  onlineManager.setOnline(true);
  setQuerySession(1, [], []);
});
afterEach(() => {
  wrappers.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
  onlineManager.setOnline(true);
});

describe('public user resource', () => {
  it('uses one normalized immutable filter snapshot for the key, request and export', async () => {
    const user = domain();
    const scope = setQuerySession(1, [], []);
    const draft = {
      userName: ' alice ',
      phonenumber: '138',
      status: '0',
      deptId: 103,
      dateRange: ['2026-10-01', '2026-10-16'],
      page: 2,
      pageSize: 20,
    };
    const filters = {
      userName: 'alice',
      phonenumber: '138',
      status: '0',
      deptId: 103,
      beginTime: '2026-10-01',
      endTime: '2026-10-16',
    };
    const options = user.userListOptions(scope, draft);
    expect(user.normalizeUserFilters(draft)).toEqual(filters);
    draft.userName = 'later';
    draft.dateRange[0] = 'later';
    vi.mocked(api.listUser).mockResolvedValue(page());
    expect(await queryClient.fetchQuery(options)).toEqual(page());
    expect(api.listUser).toHaveBeenCalledWith(
      { ...filters, page: 2, pageSize: 20 },
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
    expect(isQueryRequest(vi.mocked(api.listUser).mock.calls[0][1]?.options)).toBe(true);
    expect(options.queryKey).toEqual(
      user.userListOptions(scope, { ...filters, page: 2, pageSize: 20 }).queryKey
    );
    expect(user.normalizeUserFilters({ dateRange: null, status: '' })).toEqual({});
    expect(unref(user.userListOptions(null, {})).queryFn).toBe(skipToken);
    vi.mocked(api.deptTreeSelect).mockResolvedValue({
      items: [{ id: 1, label: '研发' }],
    });
    expect(await queryClient.fetchQuery(userDeptTreeOptions(scope))).toEqual([
      { id: 1, label: '研发' },
    ]);
  });

  it('returns a successful write before refresh and retains rows when the read fails', async () => {
    const user = domain();
    const scope = setQuerySession(1, [], []);
    vi.mocked(api.listUser).mockResolvedValue(page());
    let query!: ReturnType<typeof useQuery<Awaited<ReturnType<typeof api.listUser>>>>;
    wrappers.push(
      mount(
        defineComponent({
          setup() {
            query = useQuery(user.userListOptions(scope, { page: 1, pageSize: 10 }));
            return () => null;
          },
        }),
        { global: { plugins: [[VueQueryPlugin, { queryClient }]] } }
      )
    );
    await flushPromises();
    let fail!: (error: Error) => void;
    vi.mocked(api.listUser).mockImplementation(
      () =>
        new Promise((_, reject) => {
          fail = reject;
        })
    );
    vi.mocked(api.updateUser).mockResolvedValue(page('saved').items[0]);
    const result = await user.userCommands.updateUser(
      user.captureUserCommand({ userId: 7, nickName: 'saved' })
    );
    expect(result.userName).toBe('saved');
    await flushPromises();
    expect(query.isFetching.value).toBe(true);
    expect(query.data.value?.items[0].userName).toBe('before');
    fail(new Error('refresh failed'));
    await flushPromises();
    expect(query.error.value?.message).toBe('refresh failed');
    expect(query.data.value?.items[0].userName).toBe('before');
    expect(api.updateUser).toHaveBeenCalledTimes(1);
  });

  it('copies DTO arrays before mutation pause and rejects an old scope before sending', async () => {
    const user = domain();
    const scope = setQuerySession(1, [], []);
    const dto = { userId: 7, roleIds: [2], postIds: [3] };
    const captured = user.captureUserCommand(dto, scope);
    dto.roleIds.push(4);
    dto.postIds[0] = 9;
    expect(captured.input).toEqual({ userId: 7, roleIds: [2], postIds: [3] });
    onlineManager.setOnline(false);
    const mutation = new MutationObserver(queryClient, {
      mutationFn: user.userCommands.updateUser,
      retry: false,
    });
    const pending = mutation.mutate(captured).catch((error: unknown) => error);
    await flushPromises();
    expect(mutation.getCurrentResult().isPaused).toBe(true);
    setQuerySession(2, [], []);
    onlineManager.setOnline(true);
    await queryClient.resumePausedMutations();
    await pending;
    expect(api.updateUser).not.toHaveBeenCalled();
  });

  it('uses separate creation and detail factories and waits for stale editor data', async () => {
    const user = domain();
    const scope = setQuerySession(1, [], []);
    const options = user.userDetailOptions(scope, 7);
    queryClient.setQueryData(options.queryKey, detail(), { updatedAt: 1 });
    let complete!: (result: ReturnType<typeof detail>) => void;
    vi.mocked(api.getUser).mockImplementation(
      () =>
        new Promise((resolve) => {
          complete = resolve;
        })
    );
    let done = false;
    const read = user.readUserEditor(scope, 7).then((result) => {
      done = true;
      return result;
    });
    await flushPromises();
    expect(done).toBe(false);
    complete(detail());
    expect(await read).toEqual(detail());
    expect(isQueryRequest(vi.mocked(api.getUser).mock.calls[0][1]?.requestOptions)).toBe(true);
    vi.mocked(api.getUser).mockResolvedValue({
      ...detail(),
      data: { ...detail().data, userName: 'latest metadata' },
    });
    expect((await user.readUserEditor(scope, 7)).data?.userName).toBe('latest metadata');
    vi.mocked(api.getUser).mockResolvedValue({ posts: [], roles: [] });
    await user.readUserEditor(scope);
    expect(api.getUser).toHaveBeenLastCalledWith(
      undefined,
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
    expect(user.userCreateOptions(scope).queryKey).not.toEqual(options.queryKey);
    await expect(user.readUserEditor(null, 7)).rejects.toBeDefined();
    expect(api.getUser).toHaveBeenCalledTimes(3);
  });

  it('invalidates fresh user role membership after a role-side association write', async () => {
    const user = domain();
    expect(user.userCommands).toHaveProperty('unassignRoleUser');
    const scope = setQuerySession(1, [], []);
    vi.mocked(api.getUser).mockResolvedValue(detail());
    expect((await user.readUserEditor(scope, 7)).roleIds).toEqual([2]);
    vi.mocked(api.getUser).mockResolvedValue({ ...detail(), roleIds: [] });
    vi.mocked(roleApi.authUserCancel).mockResolvedValue(null);
    await user.userCommands.unassignRoleUser(user.captureUserCommand({ roleId: 2, userId: 7 }));
    await flushPromises();
    expect(
      queryClient.getQueryCache().find({ queryKey: user.userDetailOptions(scope, 7).queryKey })
        ?.state.isInvalidated
    ).toBe(true);
    expect((await user.readUserEditor(scope, 7)).roleIds).toEqual([]);
    expect(api.getUser).toHaveBeenCalledTimes(2);
  });

  it.each([
    'createUser',
    'updateUser',
    'deleteUsers',
    'changeStatus',
    'resetPassword',
    'assignRoles',
    'updateProfile',
    'updatePassword',
    'uploadAvatar',
    'importExcel',
  ] as const)(
    '%s invalidates the same user root for component and direct callers',
    async (name) => {
      const user = domain();
      const scope = setQuerySession(1, [], []);
      const key = [...user.userKeys.all(scope), 'probe'];
      queryClient.setQueryData(key, []);
      const input = {
        createUser: {
          userName: 'alice',
          nickName: 'Alice',
          password: 'Create123',
        },
        updateUser: { userId: 7, nickName: 'Alice' },
        deleteUsers: [7, 8],
        changeStatus: { userId: 7, status: '1' },
        resetPassword: { userId: 7, password: 'Reset123' },
        assignRoles: { userId: 7, roleIds: [2] },
        updateProfile: { nickName: 'Alice' },
        updatePassword: { oldPassword: 'Old123', newPassword: 'New123' },
        uploadAvatar: new FormData(),
        importExcel: {
          file: new File(['excel'], 'users.xlsx'),
          updateSupport: false,
        },
      }[name];
      await (
        user.userCommands[name] as (
          command: ReturnType<typeof user.captureUserCommand>
        ) => Promise<unknown>
      )(user.captureUserCommand(input));
      await flushPromises();
      expect(queryClient.getQueryCache().find({ queryKey: key })?.state.isInvalidated).toBe(true);
    }
  );
});

describe('bidirectional authorization reads', () => {
  it('shares the complete user role snapshot and invalidates both directions after a write', async () => {
    expect(userDomain).toHaveProperty('userAuthRoleOptions');
    const scope = setQuerySession(1, [], []);
    const response = {
      user: page().items[0],
      roles: [{ roleId: 2, flag: true }],
    };
    vi.mocked(api.getAuthRole).mockResolvedValue(response);
    const options = userDomain.userAuthRoleOptions(scope, '7');
    const [first, second] = await Promise.all([
      queryClient.fetchQuery(options),
      queryClient.fetchQuery(userDomain.userAuthRoleOptions(scope, 7)),
    ]);
    expect(first).toEqual(response);
    expect(second).toEqual(response);
    expect(api.getAuthRole).toHaveBeenCalledTimes(1);
    expect(isQueryRequest(vi.mocked(api.getAuthRole).mock.calls[0][1]?.requestOptions)).toBe(true);
    const list = userDomain.roleUsersOptions(scope, 2, 'allocated');
    queryClient.setQueryData(list.queryKey, page());
    await userDomain.userCommands.assignRoles(
      userDomain.captureUserCommand({ userId: 7, roleIds: [] })
    );
    await flushPromises();
    for (const key of [options.queryKey, list.queryKey])
      expect(queryClient.getQueryCache().find({ queryKey: key })?.state.isInvalidated).toBe(true);
    expect(unref(userDomain.userAuthRoleOptions(scope, 0)).enabled).toBe(false);
  });

  it('uses allocation, role and normalized paging/search snapshots as resource identity', async () => {
    expect(userDomain).toHaveProperty('roleUsersOptions');
    const scope = setQuerySession(1, [], []);
    const input = {
      userName: ' alice ',
      phonenumber: ' 138 ',
      page: '2',
      pageSize: '20',
    };
    const options = userDomain.roleUsersOptions(scope, '2', 'unallocated', input);
    expect(unref(options).staleTime).toBe(0);
    expect(unref(userDomain.roleUsersOptions(scope, '2', 'allocated', input)).staleTime).toBe(
      30_000
    );
    input.userName = 'later';
    input.page = '3';
    vi.mocked(roleApi.unallocatedUserList).mockResolvedValue(page());
    await queryClient.fetchQuery(options);
    expect(roleApi.unallocatedUserList).toHaveBeenCalledWith(
      {
        roleId: 2,
        userName: 'alice',
        phonenumber: '138',
        page: 2,
        pageSize: 20,
      },
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
    expect(isQueryRequest(vi.mocked(roleApi.unallocatedUserList).mock.calls[0][1]?.options)).toBe(
      true
    );
    expect(options.queryKey).not.toEqual(
      userDomain.roleUsersOptions(scope, 2, 'allocated', input).queryKey
    );
    vi.mocked(roleApi.allocatedUserList).mockRejectedValue(new Error('read failed'));
    await expect(
      queryClient.fetchQuery(userDomain.roleUsersOptions(scope, 2, 'allocated'))
    ).rejects.toThrow('read failed');
    expect(unref(userDomain.roleUsersOptions(null, 2, 'allocated')).enabled).toBe(false);
  });
});
