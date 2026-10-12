import { shallowRef, readonly } from 'vue';
import { useThemeAdapter, type ZxThemeJsAdapter } from '@zxio/zxui/theme-host';

interface GraphPalette {
  background: string;
  grid: string;
}

const graphTheme: ZxThemeJsAdapter<GraphPalette> = {
  id: 'ruoyi-x6-chrome',
  project({ tokens }) {
    const color = (path: string) => {
      const value = tokens[path]?.cssValue;
      if (!value) throw new Error(`Missing graph theme color: ${path}`);
      return value;
    };
    return {
      background: color('semantic.surface.page'),
      grid: color('semantic.border.subtle'),
    };
  },
};

/** Paint only presentation after the nearest Host scope commits; never update graph data. */
export function useGraphTheme() {
  const palette = shallowRef<GraphPalette>();
  useThemeAdapter(graphTheme, {
    apply(value, { signal }) {
      if (!signal.aborted) palette.value = value;
    },
  });
  return readonly(palette);
}
