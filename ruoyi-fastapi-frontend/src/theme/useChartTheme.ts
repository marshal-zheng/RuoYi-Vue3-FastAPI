import { computed } from 'vue';
import { useZxChartThemeProjection } from '@zxio/zxui/theme-host/precompiled';
import { createChartEChartsTheme } from '@zxio/chart';
import themeDeployment from 'virtual:zxui-theme-deployment';

/** Application manifest lookup only; Host and Chart own projection/color conversion. */
export function useChartTheme() {
  const result = useZxChartThemeProjection({
    resolveManifest: (themeId) =>
      themeDeployment.registrations.find(({ manifest }) => manifest.identity.themeId === themeId)
        ?.manifest,
  });
  const projection = computed(() => (result.value.ok ? result.value.value : undefined));
  const theme = computed(() =>
    projection.value ? createChartEChartsTheme(projection.value) : undefined
  );
  return { projection, theme };
}
