import { App, h } from 'vue';
import VXETable from 'vxe-table';
import 'vxe-table/lib/style.css';
import '@/components/ui/VxeTableValidation/validation.less'; // VXE-Table 通用校验样式
import VXETablePluginElement from 'vxe-table-plugin-element';
import zhCN from 'vxe-table/lib/locale/lang/zh-CN';
import VxeDictAutocomplete from '@/components/business/VxeDictAutocomplete/index.vue';

type DictRendererEvents = {
  input?: (args: Record<string, unknown>) => void;
  change?: (args: Record<string, unknown>) => void;
};

type DictRendererProps = {
  dictType?: string;
  placeholder?: string;
  disabled?: boolean;
  inputType?: string;
  clearable?: boolean;
};

type DictRendererOptions = {
  props?: DictRendererProps | ((params: DictRendererParams) => DictRendererProps);
  events?: DictRendererEvents;
};

type DictRendererRow = Record<string, string | number | undefined>;

type DictRendererParams = {
  row: DictRendererRow;
  column: { field: string };
  [key: string]: unknown;
};

export function setupVXETable(app: App) {
  VXETable.use(VXETablePluginElement);
  VXETable.setConfig({
    i18n: (key, _args) => zhCN[key],
  });

  VXETable.renderer.add('DictAutocomplete', {
    // Ensure the input is focused as soon as the cell enters edit mode
    autofocus: '.el-input__inner',
    renderEdit(renderOpts, params) {
      const option = renderOpts as DictRendererOptions;
      const typedParams = params as unknown as DictRendererParams;
      const { row, column } = typedParams;
      const field = column.field;
      const propFactory = option.props;
      const resolvedProps =
        typeof propFactory === 'function' ? propFactory(typedParams) : propFactory || {};

      const emitEvent = (eventName: 'input' | 'change', value: string | number | undefined) => {
        const handler = option.events?.[eventName];
        handler?.({
          ...(typedParams as Record<string, unknown>),
          value,
        });
      };

      const normalizeValue = (val: any) => {
        if (val && typeof val === 'object' && 'value' in val) {
          return val.value as string | number | undefined;
        }
        return val as string | number | undefined;
      };

      const handleInput = (value: any) => {
        row[field] = normalizeValue(value) ?? '';
        emitEvent('input', row[field]);
      };

      const handleChange = (value: any) => {
        row[field] = normalizeValue(value) ?? '';
        emitEvent('change', value);
      };

      return [
        h(VxeDictAutocomplete, {
          modelValue: row[field],
          'onUpdate:modelValue': handleInput,
          onChange: handleChange,
          params: {
            ...typedParams,
            ...(resolvedProps as Record<string, unknown>),
          },
        }),
      ];
    },
  });

  app.use(VXETable);
}
