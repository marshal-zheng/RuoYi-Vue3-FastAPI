import { shallowRef, watch, type Ref } from 'vue';
import type { TableInstance } from 'element-plus';
import type { ZxGridListRequestInstance } from '@zxio/zxui/grid-list';

/** The server query owns sort; ElTable only displays it and emits user intent. */
export function useGridTableSort(grid: Ref<ZxGridListRequestInstance | null | undefined>) {
  const sortTableRef = shallowRef<TableInstance>();
  let syncing = false;
  function syncSort() {
    const table = sortTableRef.value;
    if (!table) return;
    syncing = true;
    try {
      const first = grid.value?.applied?.sort[0];
      if (first) table.sort(first.field, first.order === 'asc' ? 'ascending' : 'descending');
      else table.clearSort();
    } finally {
      syncing = false;
    }
  }
  watch([() => grid.value?.applied?.sort, sortTableRef], syncSort, {
    flush: 'post',
    immediate: true,
  });
  async function onSortChange(column: { prop: string; order: 'ascending' | 'descending' | null }) {
    if (syncing) return;
    try {
      await grid.value?.requery({
        sort: column.order
          ? [
              {
                field: column.prop,
                order: column.order === 'ascending' ? 'asc' : 'desc',
              },
            ]
          : [],
        page: 1,
      });
    } finally {
      // Rejection does not publish new applied state, so explicitly restore the header too.
      syncSort();
    }
  }
  return { sortTableRef, onSortChange };
}
