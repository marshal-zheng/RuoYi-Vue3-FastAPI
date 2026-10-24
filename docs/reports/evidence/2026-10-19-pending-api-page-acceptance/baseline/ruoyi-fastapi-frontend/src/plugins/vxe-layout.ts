import { getCurrentInstance, onMounted, shallowRef, type App, type Ref } from 'vue';
import VXETable, { type VxeTableInstance } from 'vxe-table';
import {
  useDisplayLayoutParticipant,
  type ZxDisplayLayoutParticipant,
} from '@zxio/zxui/theme-host';

interface ViewportAnchor {
  readonly rowid?: string;
  readonly rowOffset: number;
  readonly scrollTop: number;
  readonly scrollLeft: number;
}

let nextParticipantId = 0;
const installed = new WeakSet<App>();

function rowHeight(table: VxeTableInstance, row: unknown): number {
  const height = table.getRowHeight(row);
  if (!Number.isFinite(height) || height <= 0) throw new Error('vxe-row-height-unresolved');
  return height;
}

/** VXE 4.17.15 public methods keep virtual offsets and CSS in one transaction. */
function captureViewport(table: VxeTableInstance): ViewportAnchor {
  const { virtualY, scrollTop, scrollLeft } = table.getScrollData();
  const fallback = { scrollTop, scrollLeft, rowOffset: 0 };
  if (!virtualY || scrollTop <= 0) return fallback;

  let rowTop = 0;
  for (const row of table.getTableData().visibleData) {
    const rowid = table.getRowid(row);
    const height = rowHeight(table, row);
    if (rowTop + height > scrollTop) {
      return {
        ...fallback,
        rowid,
        rowOffset: scrollTop - rowTop,
      };
    }
    rowTop += height;
  }
  return fallback;
}

async function restoreViewport(table: VxeTableInstance, anchor: ViewportAnchor): Promise<void> {
  let top = anchor.scrollTop;
  if (anchor.rowid && table.getRowById(anchor.rowid)) {
    let rowTop = 0;
    for (const row of table.getTableData().visibleData) {
      const rowid = table.getRowid(row);
      const height = rowHeight(table, row);
      if (rowid === anchor.rowid) {
        top = rowTop + Math.min(anchor.rowOffset, Math.max(0, height - 1));
        break;
      }
      rowTop += height;
    }
  }
  await table.scrollTo({ top, left: anchor.scrollLeft });
}

function createParticipant(
  table: VxeTableInstance,
  region: Readonly<Ref<HTMLElement | null>>
): ZxDisplayLayoutParticipant {
  return {
    id: `ruoyi-vxe-layout-${++nextParticipantId}`,
    metrics: ['spacing.control-y', 'text.body', 'text.small', 'text.extra-small'],
    async prepare(_next, signal) {
      if (signal.aborted) throw new Error('vxe-layout-stale');
      const currentRegion = region.value;
      if (!currentRegion?.isConnected) throw new Error('vxe-layout-region-disconnected');
      const anchor = captureViewport(table);
      const recalculate = async (checkSignal: boolean) => {
        if (!region.value?.isConnected) return;
        await table.recalculate(true);
        if (checkSignal && signal.aborted) return;
        await restoreViewport(table, anchor);
      };
      return {
        commit: () => recalculate(true),
        rollback: () => recalculate(false),
        dispose() {},
      };
    },
  };
}

/** Bind every table once at VXE's public created hook, within its Host scope. */
export function installVxeThemeLayout(app: App) {
  if (installed.has(app)) return;
  installed.add(app);
  const created = ({ $table }: { $table: VxeTableInstance }) => {
    // Interceptors are process-wide; only bind tables from this Vue application.
    const owner = getCurrentInstance();
    if (owner?.appContext.app !== app) return;
    const region = shallowRef<HTMLElement | null>(null);
    useDisplayLayoutParticipant(region, createParticipant($table, region));
    onMounted(() => {
      if (owner.proxy?.$el instanceof HTMLElement) region.value = owner.proxy.$el;
    });
  };
  VXETable.interceptor.add('created', created);
  const dispose = () => {
    VXETable.interceptor.delete('created', created);
    installed.delete(app);
  };
  app.onUnmount(dispose);
  import.meta.hot?.dispose(dispose);
}
