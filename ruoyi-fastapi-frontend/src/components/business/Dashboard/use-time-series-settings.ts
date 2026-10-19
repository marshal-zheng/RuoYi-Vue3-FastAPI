import { computed, ref } from 'vue';
import { cloneDashboardJson } from '@zxio/dashboard/schema';
import { readTimeSeriesChartConfig, validateTimeSeriesChartConfig } from '@zxio/dashboard-widgets';
import { parseNumberText } from '@zxio/schema-form/fields';
import type { DashboardJsonObject, DashboardJsonValue } from '@zxio/dashboard/schema';
import type { FieldMessage } from '@zxio/schema-form/fields';

/** One editor session; only valid snapshots are projected into the chart. */
export function useTimeSeriesSettings(initial: DashboardJsonObject) {
  const draft = ref(cloneDashboardJson(initial));
  const config = computed(() => readTimeSeriesChartConfig(draft.value));
  const raw = ref({
    min: String(config.value.yAxis.min),
    max: String(config.value.yAxis.max),
  });
  const messages = computed(() => {
    const result: Record<string, FieldMessage[]> = {};
    if (config.value.yAxis.mode === 'fixed') {
      for (const key of ['min', 'max'] as const) {
        if (parseNumberText(raw.value[key]).status !== 'valid') {
          result[key] = [{ severity: 'error', message: '请输入完整的有限数值' }];
        }
      }
    }
    for (const issue of validateTimeSeriesChartConfig(draft.value)) {
      const key = issue.path.split('/').at(-1)!;
      result[key] ??= [
        {
          severity: 'error',
          message: key === 'max' ? '最大值必须大于最小值' : issue.message,
        },
      ];
    }
    return result;
  });
  const valid = computed(() => !Object.keys(messages.value).length);
  const object = (value: DashboardJsonValue | undefined): DashboardJsonObject =>
    value !== null && typeof value === 'object' && !Array.isArray(value) ? value : {};
  function edit(section: string, key: string, value: DashboardJsonValue) {
    const chart = object(draft.value.chart);
    draft.value = {
      ...draft.value,
      chart: {
        ...chart,
        [section]: { ...object(chart[section]), [key]: value },
      },
    };
  }
  function editNumber(key: 'min' | 'max', text: string) {
    raw.value[key] = text;
    const parsed = parseNumberText(text);
    if (parsed.status === 'valid') edit('yAxis', key, parsed.value);
  }
  return { draft, config, raw, messages, valid, edit, editNumber };
}
