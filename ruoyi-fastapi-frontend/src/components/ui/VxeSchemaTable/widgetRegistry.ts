import type { VxeTableDefines } from 'vxe-table';
import type { VxeSchemaColumn } from './index.vue';

export type VxeWidgetResolver = (column: VxeSchemaColumn) => Partial<VxeSchemaColumn>;
export type VxeWidgetResolverMap = Record<string, VxeWidgetResolver>;

const globalRegistry: VxeWidgetResolverMap = {};

export function registerVxeWidget(name: string, resolver: VxeWidgetResolver) {
  globalRegistry[name] = resolver;
}

export function getVxeWidget(name?: string, local?: VxeWidgetResolverMap) {
  if (!name) return undefined;
  return local?.[name] ?? globalRegistry[name];
}

export function resolveWidgetColumn(
  column: VxeSchemaColumn,
  local?: VxeWidgetResolverMap
): Partial<VxeSchemaColumn> {
  const resolver = getVxeWidget(column.widget, local);
  return resolver ? resolver(column) : {};
}

const mergeEditRender = (base?: any, override?: any): any => {
  if (!base) return override;
  if (!override) return base;
  return {
    ...base,
    ...override,
    props: { ...(base.props || {}), ...(override.props || {}) },
  };
};

export function mergeColumnOptions(
  base: Partial<VxeSchemaColumn>,
  column: VxeSchemaColumn
): VxeSchemaColumn {
  const merged: VxeSchemaColumn = {
    ...base,
    ...column,
  };

  merged.editRender = mergeEditRender(base.editRender, column.editRender);

  if (base.slots || column.slots) {
    merged.slots = { ...(base.slots || {}), ...(column.slots || {}) };
  }

  return merged;
}

// 默认内置的通用组件映射
registerVxeWidget('input', () => ({
  editRender: { name: 'input' },
}));

registerVxeWidget('number', () => ({
  editRender: { name: 'input', props: { type: 'number' } },
}));

registerVxeWidget('textarea', () => ({
  editRender: { name: 'textarea' },
}));

registerVxeWidget('select', (column) => ({
  editRender: {
    name: 'select',
    props: {
      clearable: true,
      ...(column.widgetProps || {}),
    },
  },
}));

registerVxeWidget('dict-autocomplete', (column) => {
  const props = column.widgetProps || {};
  if (props.dataSource && !props.dictType) {
    // dataSource 由 schema 提供，交给组件解析
    return {
      editRender: {
        name: 'DictAutocomplete',
        props,
      },
    };
  }
  return {
    editRender: {
      name: 'DictAutocomplete',
      props: {
        placeholder: '请输入或选择',
        ...(column.widgetProps || {}),
      },
    },
  };
});
