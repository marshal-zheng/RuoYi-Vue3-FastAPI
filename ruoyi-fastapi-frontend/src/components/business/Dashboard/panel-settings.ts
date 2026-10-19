import { cloneDashboardJson } from '@zxio/dashboard/schema';
import { validateDashboardDesignerSnapshot } from '@zxio/dashboard/designer';
import { equal } from '@zxio/schema-form';
import type {
  DashboardDocument,
  DashboardJsonObject,
  DashboardPanel,
} from '@zxio/dashboard/schema';
import type { DashboardPersistence } from '@zxio/dashboard/persistence';
import type { DashboardWidgetRegistry } from '@zxio/dashboard/widget';

export interface PanelSettingsSession {
  panel: DashboardPanel;
  save: (params: DashboardJsonObject) => Promise<void>;
}

/** The persistence controller remains the sole owner of the loaded revision. */
export function beginPanelSettings(
  controller: DashboardPersistence,
  getDocument: () => DashboardDocument,
  registry: DashboardWidgetRegistry,
  panelId: string
): PanelSettingsSession {
  const initial = controller.getState();
  const original = getDocument().panels.find((panel) => panel.id === panelId);
  if (!original || initial.pending || initial.conflict) throw new Error('请先完成布局同步');
  const panel = cloneDashboardJson(original);
  const revision = initial.saved?.revision ?? null;
  return {
    panel,
    async save(params) {
      const state = controller.getState();
      const current = getDocument();
      const target = current.panels.find((item) => item.id === panelId);
      if (
        state.pending ||
        state.conflict ||
        (state.saved?.revision ?? null) !== revision ||
        !target ||
        target.widget !== panel.widget ||
        target.variant !== panel.variant ||
        !equal(target.params ?? {}, panel.params ?? {})
      )
        throw new Error('图表或服务器版本已变化，请取消后重新打开设置');
      const candidate = cloneDashboardJson(current);
      candidate.panels.find((item) => item.id === panelId)!.params = cloneDashboardJson(params);
      const validation = validateDashboardDesignerSnapshot({
        document: candidate,
        panels: candidate.panels,
        registry,
      });
      if (!validation.valid)
        throw new Error(validation.issues.map((issue) => issue.message).join('；'));
      const result = await controller.save(candidate);
      if (result.status !== 'saved')
        throw new Error('服务器版本冲突，请取消设置并处理布局冲突后重试');
    },
  };
}
