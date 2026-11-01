import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { ref } from 'vue';
import ElementPlus from 'element-plus';
import { createShortcutRuntime } from '@zxio/keybindings';
import { createShortcutPlugin } from '@zxio/keybindings/vue';
import { VueQueryPlugin } from '@tanstack/vue-query';
import SelectUser from '@/views/system/role/selectUser.vue';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import { unallocatedUserList } from '@/api/system/role';

vi.mock('@/api/system/role', () => ({ unallocatedUserList: vi.fn() }));
vi.mock('@/utils/permission', () => ({ checkPermi: () => true }));
const mounted: ReturnType<typeof mount>[] = [];
beforeEach(() => {
  queryClient.clear();
  setQuerySession(1, ['admin'], ['*:*:*']);
  vi.mocked(unallocatedUserList).mockImplementation(
    async (params) =>
      ({
        items:
          params?.page === 2
            ? [{ userId: 3, userName: 'third' }]
            : [
                { userId: 1, userName: 'root' },
                { userId: 2, userName: 'second' },
              ],
        total: 11,
        page: Number(params?.page ?? 1),
        pageSize: 10,
      }) as never
  );
});
afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
});
it('uses the real selector for header eligibility, missing IDs, row clicks and a new dialog session', async () => {
  const wrapper = mount(SelectUser, {
    props: { roleId: 20 },
    global: {
      plugins: [
        ElementPlus,
        [VueQueryPlugin, { queryClient }],
        createShortcutPlugin(
          createShortcutRuntime({ appId: 'table-selection-test', platform: 'mac' })
        ),
      ],
      config: { globalProperties: { useDict: () => ({ sys_normal_disable: ref([]) }) } as never },
      stubs: {
        ZxDialog: { template: '<div><slot /><slot name="footer" /></div>' },
        DictStatus: true,
        DictTag: true,
      },
    },
  });
  mounted.push(wrapper);
  wrapper.vm.show();
  await flushPromises();
  const list = () => wrapper.getComponent({ name: 'ZxTableRender' });
  const api = () =>
    list().vm as unknown as {
      selection: { keys: number[]; missingKeys: number[]; scopeRef: string };
      requery(change: { page: number }): Promise<unknown>;
    };
  const table = () => wrapper.getComponent({ name: 'ElTable' });
  await table().get('thead input[type=checkbox]').setValue(true);
  expect(api().selection.keys).toEqual([2]);
  expect((table().findAll('tbody input')[0].element as HTMLInputElement).disabled).toBe(true);
  const opening = api().selection.scopeRef;
  await api().requery({ page: 2 });
  await flushPromises();
  expect(table().props('data')[0].userId).toBe(3);
  expect(api().selection.missingKeys).toEqual([2]);
  await table().get('tbody tr').trigger('click');
  await flushPromises();
  expect(api().selection.keys).toEqual([2, 3]);
  const cancel = wrapper
    .findAll('button')
    .find((button) => button.text().replace(/\s/g, '') === '取消')!;
  await cancel.trigger('click');
  wrapper.vm.show();
  await flushPromises();
  expect(api().selection.keys).toEqual([]);
  expect(api().selection.scopeRef).not.toBe(opening);
});
