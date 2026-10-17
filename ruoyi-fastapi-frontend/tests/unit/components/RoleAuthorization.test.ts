import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { flushPromises, shallowMount } from '@vue/test-utils';
import * as vue from 'vue';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { useRoute } from 'vue-router';
import type { ComponentCustomProperties } from 'vue';
import { getAuthRole } from '@/api/system/user';
import { allocatedUserList, unallocatedUserList } from '@/api/system/role';
import AuthRole from '@/views/system/user/authRole.vue';
import AuthUser from '@/views/system/role/authUser.vue';
import SelectUser from '@/views/system/role/selectUser.vue';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';

const api = vi.hoisted(() => ({
  assign: vi.fn(),
  grant: vi.fn(),
  revoke: vi.fn(),
  batch: vi.fn(),
}));
vi.mock('@/api/system/user', () => ({
  getAuthRole: vi.fn().mockResolvedValue({ user: { userId: 42 }, roles: [] }),
  updateAuthRole: api.assign,
}));
vi.mock('@/api/system/role', () => ({
  allocatedUserList: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  unallocatedUserList: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  authUserSelectAll: api.grant,
  authUserCancel: api.revoke,
  authUserCancelAll: api.batch,
}));
vi.mock('vue-router', () => ({ useRoute: vi.fn() }));
vi.mock('@/utils/permission', () => ({
  checkPermi: vi.fn(() => true),
  checkRole: vi.fn(() => true),
}));
const mounted: ReturnType<typeof shallowMount>[] = [];
const confirm = vi.fn<() => Promise<unknown>>();
function page(component: typeof AuthRole, props = {}) {
  const wrapper = shallowMount(
    { ...component, render: () => null },
    {
      props,
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        config: {
          globalProperties: {
            useDict: () => ({ sys_normal_disable: vue.ref([]) }),
            $tab: { closeOpenPage: vi.fn() },
            $modal: { confirm },
          } as unknown as ComponentCustomProperties,
        },
      },
    }
  );
  mounted.push(wrapper);
  return (
    wrapper.vm as unknown as {
      $: {
        setupState: {
          cancelAuthUser(row: { userId: number; userName: string }): Promise<void>;
          cancelAuthUserAll(): Promise<void>;
          handleSelectionChange(rows: { roleId?: number; userId?: number }[]): void;
          handleSave(): Promise<void>;
          show(): void;
          handleSelectUser(): Promise<void>;
        };
      };
    }
  ).$.setupState;
}
beforeEach(() => {
  queryClient.clear();
  setQuerySession(1, [], []);
  confirm.mockResolvedValue(undefined);
  vi.clearAllMocks();
  vi.mocked(getAuthRole).mockResolvedValue({
    user: { userId: 42 },
    roles: [{ roleId: 20, roleName: 'staff' }],
  } as never);
  vi.mocked(allocatedUserList).mockResolvedValue({
    items: [],
    total: 0,
  } as never);
  vi.mocked(unallocatedUserList).mockResolvedValue({
    items: [],
    total: 0,
  } as never);
  for (const f of Object.values(api)) f.mockResolvedValue(null);
  for (const key of ['ref', 'reactive', 'getCurrentInstance', 'nextTick'])
    vi.stubGlobal(key, vue[key as keyof typeof vue]);
  vi.mocked(useRoute).mockReturnValue({
    params: { userId: '42', roleId: '20' },
  } as never);
});
afterEach(() => {
  mounted.splice(0).forEach((w) => w.unmount());
  endQuerySession();
  queryClient.clear();
});

it('does not send a role revoke confirmed after the opening scope ended', async () => {
  let accept!: () => void;
  confirm.mockReturnValueOnce(
    new Promise<void>((resolve) => {
      accept = resolve;
    })
  );
  const s = page(AuthUser);
  const task = s.cancelAuthUser({ userId: 42, userName: 'alice' });
  await flushPromises();
  setQuerySession(2, [], []);
  accept();
  await task;
  expect(api.revoke).not.toHaveBeenCalled();
});

it('user role page submits full selection and an explicit empty array', async () => {
  const s = page(AuthRole);
  await flushPromises();
  s.handleSelectionChange([{ roleId: 20 }]);
  await s.handleSave();
  expect(api.assign.mock.calls.at(-1)?.[0]).toEqual({
    userId: 42,
    roleIds: [20],
  });
  s.handleSelectionChange([]);
  await s.handleSave();
  expect(api.assign.mock.calls.at(-1)?.[0]).toEqual({
    userId: 42,
    roleIds: [],
  });
});
it('role page revokes only the selected relation(s) with numeric route ID', async () => {
  const s = page(AuthUser);
  await s.cancelAuthUser({ userId: 42, userName: 'alice' });
  expect(api.revoke.mock.calls[0][0]).toEqual({ roleId: 20, userId: 42 });
  s.handleSelectionChange([{ userId: 42 }, { userId: 43 }]);
  await s.cancelAuthUserAll();
  expect(api.batch.mock.calls[0][0]).toEqual({ roleId: 20, userIds: [42, 43] });
});
it('selector submits an incremental array using numeric role ID', async () => {
  const s = page(SelectUser, { roleId: '20' });
  s.show();
  s.handleSelectionChange([{ userId: 42 }, { userId: 43 }]);
  await s.handleSelectUser();
  expect(api.grant.mock.calls[0][0]).toEqual({ roleId: 20, userIds: [42, 43] });
});
