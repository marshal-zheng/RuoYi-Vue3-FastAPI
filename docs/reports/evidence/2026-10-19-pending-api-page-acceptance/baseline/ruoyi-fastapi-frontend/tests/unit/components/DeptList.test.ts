import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { onlineManager, VueQueryPlugin } from '@tanstack/vue-query';
import { defineComponent, h, nextTick, type ComponentCustomProperties } from 'vue';
import DeptList from '@/views/system/dept/components/DeptList.vue';
import { delDept, listDept } from '@/api/system/dept';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import { handleTree } from '@/utils/ruoyi';

vi.mock('@/api/system/dept', () => ({
  listDept: vi.fn(),
  getDept: vi.fn(),
  listDeptExcludeChild: vi.fn(),
  addDept: vi.fn(),
  updateDept: vi.fn(),
  delDept: vi.fn(),
}));
const confirm = vi.fn();
const slot = {
  template:
    '<div><slot /><slot name="actions" /><slot name="filters" /><slot name="search" /></div>',
};
const filter = defineComponent({
  name: 'DeptFilter',
  props: ['modelValue'],
  template: '<input />',
});
const search = defineComponent({
  name: 'DeptSearch',
  props: ['modelValue'],
  template: '<button />',
});
const grid = defineComponent({
  name: 'DeptGrid',
  props: ['mode', 'rows', 'status', 'loadData'],
  emits: ['refresh'],
  setup(props, { slots }) {
    return () =>
      h('div', [
        slots.form?.({ query: {} }),
        slots.table?.({
          grid: { list: props.rows, loading: props.status?.loading },
          renderEmpty: () => h('span', 'query-empty-presentation'),
        }),
      ]);
  },
});
const table = defineComponent({
  name: 'DeptTable',
  props: ['data'],
  setup(_, { slots }) {
    return () => h('div', [slots.default?.(), slots.empty?.()]);
  },
});
const mounted: ReturnType<typeof mount>[] = [];
function mountList() {
  const wrapper = mount(DeptList, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      config: {
        globalProperties: {
          useDict: () => ({}),
          handleTree,
          $modal: { confirm },
        } as unknown as ComponentCustomProperties,
      },
      directives: { hasPermi: () => {}, loading: () => {} },
      stubs: {
        ZxGridList: grid,
        ZxListToolbar: slot,
        DictSelect: filter,
        ZxSearch: search,
        ZxInput: filter,
        ZxButton: slot,
        DeptDlg: true,
        DictStatus: true,
        ElTable: table,
        ElTableColumn: defineComponent({
          setup(_, { slots }) {
            return () =>
              h(
                'div',
                slots.default?.({
                  row: { deptId: 2, parentId: 1, deptName: 'Child' },
                })
              );
          },
        }),
        DictTag: true,
        ZxMoreAction: true,
      },
    },
  });
  mounted.push(wrapper);
  return wrapper;
}
beforeEach(() => {
  vi.resetAllMocks();
  queryClient.clear();
  setQuerySession(1, [], []);
  onlineManager.setOnline(true);
  vi.mocked(listDept).mockResolvedValue({
    items: [{ deptId: 1, parentId: 0, deptName: 'Root' }],
  });
});
afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
  onlineManager.setOnline(true);
});

describe('department list resource integration', () => {
  it('captures the deleting session before confirmation and refuses a later session', async () => {
    let accept!: () => void;
    confirm.mockReturnValueOnce(
      new Promise<void>((resolve) => {
        accept = resolve;
      })
    );
    const wrapper = mountList();
    await flushPromises();
    wrapper.findComponent({ name: 'ZxMoreAction' }).vm.$emit('select', { eventTag: 'delete' });
    await flushPromises();
    expect(confirm).toHaveBeenCalledTimes(1);
    setQuerySession(2, [], []);
    accept();
    await flushPromises();
    expect(delDept).not.toHaveBeenCalled();
  });

  it('refreshes successful deletes through the resource command once', async () => {
    confirm.mockResolvedValueOnce(undefined);
    vi.mocked(delDept).mockResolvedValueOnce(null);
    const wrapper = mountList();
    await flushPromises();
    wrapper.findComponent({ name: 'ZxMoreAction' }).vm.$emit('select', { eventTag: 'delete' });
    await flushPromises();
    expect(delDept).toHaveBeenCalledTimes(1);
    expect(listDept).toHaveBeenCalledTimes(2);
  });

  it('uses controlled rows and copies flat cached records before tree projection', async () => {
    const rows = Object.freeze([
      Object.freeze({ deptId: 1, parentId: 0, deptName: 'Root' }),
      Object.freeze({ deptId: 2, parentId: 1, deptName: 'Child' }),
    ]);
    vi.mocked(listDept).mockResolvedValue({ items: rows as never });
    const wrapper = mountList();
    await flushPromises();
    expect(wrapper.findComponent(grid).props('mode')).toBe('controlled');
    expect(wrapper.findComponent(grid).props('loadData')).toBeUndefined();
    expect(wrapper.findComponent(grid).props('rows')).toEqual([
      { ...rows[0], children: [rows[1]] },
    ]);
    expect(rows[0]).not.toHaveProperty('children');
    expect(wrapper.text()).toContain('query-empty-presentation');
  });
  it('keeps edits local until submit and normalizes the submitted filters', async () => {
    const wrapper = mountList();
    await flushPromises();
    expect(listDept).toHaveBeenCalledTimes(1);
    wrapper.findAllComponents(filter)[0].vm.$emit('update:modelValue', '  研发  ');
    await nextTick();
    expect(listDept).toHaveBeenCalledTimes(1);
    wrapper.findComponent(search).vm.$emit('search');
    await flushPromises();
    expect(vi.mocked(listDept).mock.calls.at(-1)?.[0]).toEqual({
      deptName: '研发',
    });
    const select = wrapper.findAllComponents(filter)[1];
    select.vm.$emit('update:modelValue', '1');
    select.vm.$emit('change', '1');
    await flushPromises();
    expect(vi.mocked(listDept).mock.calls.at(-1)?.[0]).toEqual({
      deptName: '研发',
      status: '1',
    });
  });
  it('keeps successful rows and reports a same-filter refresh failure', async () => {
    const wrapper = mountList();
    await flushPromises();
    vi.mocked(listDept).mockRejectedValueOnce(new Error('refresh failed'));
    wrapper.findComponent(grid).vm.$emit('refresh');
    await flushPromises();
    expect(wrapper.findComponent(grid).props('rows')).toMatchObject([{ deptName: 'Root' }]);
    expect(wrapper.findComponent(grid).props('status')).toMatchObject({
      error: expect.objectContaining({ message: 'refresh failed' }),
      loading: false,
    });
  });
  it('reports a first failure through status and the public empty renderer', async () => {
    vi.mocked(listDept).mockRejectedValueOnce(new Error('read failed'));
    const wrapper = mountList();
    await flushPromises();
    expect(wrapper.findComponent(grid).props('status')).toMatchObject({
      error: expect.objectContaining({ message: 'read failed' }),
      loading: false,
    });
    expect(wrapper.text()).toContain('query-empty-presentation');
  });
  it('exposes a paused read without reporting empty success', async () => {
    onlineManager.setOnline(false);
    const wrapper = mountList();
    await flushPromises();
    expect(wrapper.findComponent(grid).props('status')).toMatchObject({
      paused: true,
    });
    expect(listDept).not.toHaveBeenCalled();
  });
});
