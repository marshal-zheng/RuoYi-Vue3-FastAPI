import type {
  DictAutocompleteCellParams,
  DictAutocompleteRenderOptions,
  DictEditorValue,
  DictEditorRow,
} from '@/components/business/VxeDictAutocomplete/types';
import { getCurrentInstance, h, type App } from 'vue';
import VXETable from 'vxe-table';
import 'vxe-table/lib/style.css';
import '@zxio/zxui/style/vxe-table.css';
import '@/components/ui/VxeTableValidation/validation.less'; // VXE-Table 通用校验样式
import VXETablePluginElement from 'vxe-table-plugin-element';
import zhCN from 'vxe-table/lib/locale/lang/zh-CN';
import VxeDictAutocomplete from '@/components/business/VxeDictAutocomplete/index.vue';
import { installVxeThemeLayout } from './vxe-layout';

type DictRendererRow = DictEditorRow;
const installed = new WeakSet<App>();
let runtimeConfigured = false;

/** Register synchronously before a table consumer's first render. */
export function useVXETable() {
  const instance = getCurrentInstance();
  if (!instance) throw new Error('useVXETable must be called during component setup');
  setupVXETable(instance.appContext.app);
}

/** VXE owns one process-wide renderer and locale registry. */
function configureVXETable() {
  if (runtimeConfigured) return;
  VXETable.use(VXETablePluginElement);
  VXETable.setI18n('zh-CN', zhCN);
  VXETable.setLanguage('zh-CN');

  VXETable.renderer.add('DictAutocomplete', {
    // Ensure the input is focused as soon as the cell enters edit mode
    autofocus: '.el-input__inner',
    renderEdit(renderOpts, params) {
      const option = renderOpts as DictAutocompleteRenderOptions<DictRendererRow>;
      const typedParams: DictAutocompleteCellParams<DictRendererRow> = params;
      const { row, column } = typedParams;
      const field = column.field;
      const propFactory = option.props;
      const resolvedProps =
        typeof propFactory === 'function' ? propFactory(typedParams) : propFactory || {};

      const emitEvent = (eventName: 'input' | 'change', value: DictEditorValue) => {
        const handler = option.events?.[eventName];
        handler?.({
          ...typedParams,
          value,
        });
      };

      const normalizeValue = (value: unknown): string | number | undefined => {
        const scalar = value && typeof value === 'object' && 'value' in value ? value.value : value;
        return typeof scalar === 'string' || typeof scalar === 'number' ? scalar : undefined;
      };

      const handleInput = (value: string | number | undefined) => {
        row[field] = normalizeValue(value) ?? '';
        emitEvent('input', normalizeValue(row[field]));
      };

      const handleChange = (value: DictEditorValue) => {
        row[field] = normalizeValue(value) ?? '';
        emitEvent('change', value);
      };

      return [
        h(VxeDictAutocomplete, {
          modelValue: normalizeValue(row[field]),
          'onUpdate:modelValue': handleInput,
          onChange: handleChange,
          params: {
            ...typedParams,
            ...resolvedProps,
          },
        }),
      ];
    },
  });

  runtimeConfigured = true;
}

export function setupVXETable(app: App) {
  if (installed.has(app)) return;
  configureVXETable();
  installVxeThemeLayout(app);
  app.use(VXETable);
  installed.add(app);
}
