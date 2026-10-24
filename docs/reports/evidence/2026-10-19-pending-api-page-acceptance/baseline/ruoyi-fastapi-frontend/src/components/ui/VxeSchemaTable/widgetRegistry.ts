import type { DataSourceItem } from './dataSource';
import type { VxeSchemaColumn } from './types';

export type VxeWidgetResolver = <Row extends object>(
  column: VxeSchemaColumn<Row>
) => Partial<VxeSchemaColumn<Row>>;
export type VxeWidgetResolverMap = Record<string, VxeWidgetResolver>;

const globalRegistry: VxeWidgetResolverMap = {};

export function registerVxeWidget(name: string, resolver: VxeWidgetResolver) {
  globalRegistry[name] = resolver;
}

export function getVxeWidget(name?: string, local?: VxeWidgetResolverMap) {
  if (!name) return undefined;
  return local?.[name] ?? globalRegistry[name];
}

export function resolveWidgetColumn<Row extends object = DataSourceItem>(
  column: VxeSchemaColumn<Row>,
  local?: VxeWidgetResolverMap
): Partial<VxeSchemaColumn<Row>> {
  const resolver = getVxeWidget(column.widget, local);
  return resolver ? resolver(column) : {};
}

type EditRender<Row extends object> = VxeSchemaColumn<Row>['editRender'];
const mergeEditRender = <Row extends object>(
  base?: EditRender<Row>,
  override?: EditRender<Row>
): EditRender<Row> => {
  if (!base) return override;
  if (!override) return base;
  return {
    ...base,
    ...override,
    props: { ...(base.props || {}), ...(override.props || {}) },
  };
};

export function mergeColumnOptions<Row extends object>(
  base: Partial<VxeSchemaColumn<Row>>,
  column: VxeSchemaColumn<Row>
): VxeSchemaColumn<Row> {
  const merged: VxeSchemaColumn<Row> = {
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
