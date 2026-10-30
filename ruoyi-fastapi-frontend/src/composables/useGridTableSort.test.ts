import { expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick, shallowRef } from 'vue';
import { mount } from '@vue/test-utils';
import {
  ZxGridList,
  type GridListQueryValidator,
  type ZxGridListRequestInstance,
} from '@zxio/zxui/grid-list';
import { useGridTableSort } from './useGridTableSort';
import type { TableInstance } from 'element-plus';

it('synchronizes accepted owner sorting and restores a rejected sort without a request loop', async () => {
  const grid = shallowRef<ZxGridListRequestInstance>();
  const load = vi.fn(async () => ({ list: [{ id: 1 }], total: 1 }));
  let sorting!: ReturnType<typeof useGridTableSort>;
  const wrapper = mount(
    defineComponent({
      setup() {
        sorting = useGridTableSort(grid);
        return () =>
          h(
            ZxGridList,
            {
              ref: grid,
              loadData: load,
              loadOnMounted: false,
              debounceDelay: 0,
              defaults: { sort: [{ field: 'id', order: 'desc' }] },
              queryValidator: (({ sort }) =>
                sort.some((item) => item.field !== 'id')
                  ? [{ path: ['sort'], code: 'invalid-field' }]
                  : null) satisfies GridListQueryValidator,
            },
            { table: () => h('div') }
          );
      },
    }),
    { global: { stubs: { ElPagination: true } } }
  );
  const appliedHeader = { field: '', order: '' };
  sorting.sortTableRef.value = {
    sort(field: string, order: 'ascending' | 'descending') {
      Object.assign(appliedHeader, { field, order });
      void sorting.onSortChange({ prop: field, order });
    },
    clearSort() {
      Object.assign(appliedHeader, { field: '', order: '' });
    },
  } as TableInstance;
  await grid.value!.reset({ immediate: true });
  await nextTick();
  expect(appliedHeader).toEqual({ field: 'id', order: 'descending' });
  expect(load).toHaveBeenCalledTimes(1);
  await sorting.onSortChange({ prop: 'id', order: 'ascending' });
  await nextTick();
  expect(load).toHaveBeenCalledTimes(2);
  expect(grid.value!.applied?.sort).toEqual([{ field: 'id', order: 'asc' }]);
  await sorting.onSortChange({ prop: 'forbidden', order: 'descending' });
  expect(load).toHaveBeenCalledTimes(2);
  expect(appliedHeader).toEqual({ field: 'id', order: 'ascending' });
  wrapper.unmount();
});
