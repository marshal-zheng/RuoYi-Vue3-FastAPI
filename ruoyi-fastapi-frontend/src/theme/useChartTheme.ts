import { computed } from 'vue';
import { useZxChartThemeProjection } from '@zxio/zxui/theme-host/precompiled';
import { createChartEChartsTheme } from '@zxio/chart';

/** Host owns the nearest scope registration; Chart owns color conversion. */
export function useChartTheme() {
  const result = useZxChartThemeProjection();
  const projection = computed(() => (result.value.ok ? result.value.value : undefined));
  const theme = computed(() =>
    projection.value ? createChartEChartsTheme(projection.value) : undefined
  );
  return { projection, theme };
}
