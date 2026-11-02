import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { ref } from 'vue';
import ElementPlus from 'element-plus';
import { createShortcutRuntime } from '@zxio/keybindings';
import { createShortcutPlugin } from '@zxio/keybindings/vue';
import { VueQueryPlugin } from '@tanstack/vue-query';
import type { TableRenderInstance } from '@zxio/table-render/ui';
import DeptList from '@/views/system/dept/components/DeptList.vue';
import { listDept } from '@/api/system/dept';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';

vi.mock('@/api/system/dept', () => ({ listDept: vi.fn() }));
const rows = Object.freeze([
  Object.freeze({ deptId: 1, parentId: 0, deptName: 'Root' }),
  Object.freeze({ deptId: 2, parentId: 1, deptName: 'Child' }),
]);
const mounted: ReturnType<typeof mount>[] = [];
beforeEach(() => {
  queryClient.clear();
  setQuerySession(1, [], []);
  vi.mocked(listDept).mockResolvedValue({ items: rows as never });
});
afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
});
it('preserves cached records and the table instance, clears expansion while the domain changes, and defaults the new successful tree', async () => {
  const wrapper = mount(DeptList, {
    global: {
      plugins: [
        ElementPlus,
        [VueQueryPlugin, { queryClient }],
        createShortcutPlugin(createShortcutRuntime({ appId: 'table-tree-test', platform: 'mac' })),
      ],
      config: { globalProperties: { useDict: () => ({ sys_normal_disable: ref([]) }) } as never },
      directives: { hasPermi: () => {} },
      stubs: {
        DeptDlg: true,
        DictStatus: true,
        DictSelect: true,
        DictTag: true,
        ZxMoreAction: true,
        ZxButton: {
          emits: ['click'],
          template: '<button @click="$emit(\'click\')"><slot /></button>',
        },
      },
    },
  });
  mounted.push(wrapper);
  await flushPromises();
  const table = wrapper.getComponent({ name: 'ElTable' });
  // The public API is the parent's template ref. VTU child.vm is only the
  // internal proxy for a packed SFC whose setup returns a render function.
  const api = wrapper.vm.$refs.refTable as Pick<
    TableRenderInstance<unknown, unknown, unknown>,
    'expandedKeys' | 'setExpandedKeys'
  >;
  const instance = table.vm;
  expect(api.expandedKeys).toEqual([1]);
  expect(table.props('data')).toEqual([{ ...rows[0], children: [rows[1]] }]);
  expect(rows[0]).not.toHaveProperty('children');
  const toggle = wrapper.findAll('button').find((button) => button.text() === '展开/折叠')!;
  await toggle.trigger('click');
  await flushPromises();
  expect(api.expandedKeys).toEqual([]);
  await toggle.trigger('click');
  await flushPromises();
  expect(api.expandedKeys).toEqual([1]);
  expect(wrapper.getComponent({ name: 'ElTable' }).vm).toBe(instance);
  expect(listDept).toHaveBeenCalledTimes(1);
  let releaseNext!: () => void;
  vi.mocked(listDept).mockImplementationOnce(
    () =>
      new Promise((resolve) => {
        releaseNext = () => resolve({ items: rows as never });
      })
  );
  setQuerySession(2, [], []);
  await flushPromises();
  expect(api.expandedKeys).toEqual([]);
  expect(table.props('data')).toEqual([]);
  releaseNext();
  await flushPromises();
  expect(api.expandedKeys).toEqual([1]);
  expect(table.props('data')).toHaveLength(1);
});
