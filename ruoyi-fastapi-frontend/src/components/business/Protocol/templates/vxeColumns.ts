import type { VxeTableDefines } from 'vxe-table';

type DataTypeEditProps = {
  dictType?: string;
  placeholder?: string;
  uppercaseLabel?: boolean;
};

type FieldColumnsOptions = {
  dataTypeProps?: DataTypeEditProps;
};

const DEFAULT_DATA_TYPE_PROPS: Required<Pick<DataTypeEditProps, 'dictType' | 'placeholder'>> &
  DataTypeEditProps = {
  dictType: 'sys_protocol_data_type',
  placeholder: '请输入或选择',
};

export const createProtocolFieldColumns = (
  options: FieldColumnsOptions = {}
): VxeTableDefines.ColumnOptions[] => {
  const dataTypeProps = {
    ...DEFAULT_DATA_TYPE_PROPS,
    ...(options.dataTypeProps ?? {}),
  };

  return [
    { type: 'checkbox', fixed: 'left', width: 50 },
    { type: 'seq', title: '序号', treeNode: true, width: 80 },
    { field: 'fieldName', title: '信息名称', editRender: { name: 'input' } },
    {
      field: 'byteCount',
      title: '字节数',
      width: 100,
      editRender: { name: 'input', props: { type: 'number' } },
    },
    { field: 'byteSequence', title: '字节序号', width: 120 },
    { field: 'valueRange', title: '值域及含义', editRender: { name: 'textarea' } },
    { field: 'unit', title: '量纲', width: 100, editRender: { name: 'input' } },
    {
      field: 'dataType',
      title: '数据类型',
      width: 140,
      editRender: {
        name: 'DictAutocomplete',
        props: dataTypeProps,
      },
    },
    { field: 'scale', title: '比例尺', width: 100, editRender: { name: 'input' } },
    { field: 'remark', title: '备注', editRender: { name: 'input' } },
  ];
};

export const createProtocolConfigColumns = (
  editRender: (field: 'value1' | 'value2') => VxeTableDefines.EditRender | undefined
): VxeTableDefines.ColumnOptions[] => [
  { field: 'protocolName', title: '', width: 80, align: 'center' },
  { field: 'label1', title: '', width: 120, align: 'center' },
  { field: 'value1', title: '', minWidth: 200, editRender: editRender('value1') },
  { field: 'label2', title: '', width: 140, align: 'center' },
  { field: 'value2', title: '', minWidth: 200, editRender: editRender('value2') },
];
