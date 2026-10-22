import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { ElCheckbox, ElTree } from 'element-plus';
import RoleDataScopeDrawer from '@/views/system/role/components/RoleDataScopeDrawer.vue';
import { dataScope, deptTreeSelect, getRole } from '@/api/system/role';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';

vi.mock('@/api/system/role', () => ({
  dataScope: vi.fn(),
  deptTreeSelect: vi.fn(),
  getRole: vi.fn(),
}));

const slot = { template: '<div><slot /></div>' };
const wrappers: ReturnType<typeof mount>[] = [];
beforeEach(() => {
  queryClient.clear();
  setQuerySession(1, ['admin'], ['*:*:*']);
  vi.mocked(getRole).mockResolvedValue({
    roleId: 94,
    roleName: 'Department reader',
    roleKey: 'reader',
    dataScope: '2',
    deptCheckStrictly: true,
  } as never);
  vi.mocked(deptTreeSelect).mockResolvedValue({
    depts: [
      {
        id: 100,
        label: 'Group',
        children: [
          {
            id: 101,
            label: 'Company',
            children: [
              { id: 103, label: 'Research' },
              { id: 104, label: 'Sales' },
            ],
          },
        ],
      },
    ],
    checkedKeys: [],
  });
  vi.mocked(dataScope).mockResolvedValue({
      remarkText: '',
    roleId: 94,
    roleName: 'Department reader',
    roleKey: 'reader',
    roleSort: 0,
    status: '0',
    dataScope: '2',
  });
});
afterEach(() => {
  wrappers.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
});

it('submits only checked departments, excluding partially checked ancestors from the grant', async () => {
  const wrapper = mount(RoleDataScopeDrawer, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      components: { ElCheckbox, ElTree },
      stubs: {
        ZxDrawer: {
          ...slot,
          name: 'ZxDrawer',
          props: ['loading', 'okDisabled', 'confirm'],
        },
        ElForm: slot,
        ElFormItem: slot,
        ElAlert: slot,
        ElButton: slot,
        ElSelect: slot,
        ElOption: true,
        ElCheckbox: false,
        ZxInput: true,
      },
    },
  });
  wrappers.push(wrapper);
  await (wrapper.vm as unknown as { open(id: number): Promise<void> }).open(94);
  await flushPromises();
  const tree = wrapper.findComponent(ElTree);
  await tree.findAll('input[type=checkbox]')[2]!.setValue(true);
  expect(tree.vm.getCheckedKeys()).toEqual([103]);
  expect(tree.vm.getHalfCheckedKeys()).toEqual([100, 101]);
  await wrapper.findComponent({ name: 'ZxDrawer' }).props('confirm')();
  await flushPromises();
  expect(dataScope).toHaveBeenCalledWith(
    { roleId: 94, dataScope: '2', deptCheckStrictly: true, deptIds: [103] },
    expect.anything()
  );
});
